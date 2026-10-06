// import_soc.js – handling file upload, auto‑detect, preview, and import
// Supports both .xlsx (Excel) and .csv formats

let selectedFile = null;
let detectedTemplate = null;
let detectedPeriod = null;
let parsedRows = [];
let allSheetData = {};  // Store all sheet data for sheet selection

function $(id){return document.getElementById(id);}
function show(element){if(element){element.style.display='block';}else{console.warn('show() - element not found');}}
function hide(element){if(element){element.style.display='none';}else{console.warn('hide() - element not found');}}
function setHTML(id, html){const el=$(id);if(el){el.innerHTML=html;}}

$('soc-file-input').addEventListener('change', async (e)=>{
    const file = e.target.files[0];
    if(!file) return;
    selectedFile = file;
    setHTML('file-info', `File terpilih: <strong>${file.name}</strong>`);
    await processFile(file);
});

async function processFile(file){
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    if(fileExt === 'csv'){
        await processCSV(file);
    }else if(fileExt === 'xlsx' || fileExt === 'xls'){
        await processExcel(file);
    }else{
        showToast('Format file tidak didukung. Gunakan .xlsx atau .csv', 'error');
    }
}

async function processExcel(file){
    const reader = new FileReader();
    reader.onload = async (e)=>{
        const data = e.target.result;
        const wb = XLSX.read(data, {type:'binary'});
        
        // Scan all sheets and detect template type for each
        const sheetDetections = [];
        allSheetData = {};
        
        for(const sheetName of wb.SheetNames){
            const ws = wb.Sheets[sheetName];
            const json = XLSX.utils.sheet_to_json(ws, {defval: ''});
            if(json.length === 0) continue;
            
            const headers = Object.keys(json[0]);
            
            // Call backend to detect template
            try {
                const detectRes = await apiPost('/api/import/soc/detect', {headers});
                const template = detectRes.template_type;
                const confidence = detectRes.confidence;
                
                if(template !== 'unknown' && confidence > 0.5){
                    sheetDetections.push({
                        sheetName: sheetName,
                        template: template,
                        confidence: confidence,
                        data: json,
                        headers: headers
                    });
                    allSheetData[sheetName] = {template, confidence, data: json, headers};
                }
            }catch(err){
                console.warn('Failed to detect template for sheet ' + sheetName + ': ' + err.message);
            }
        }
        
        if(sheetDetections.length === 0){
            showToast('Tidak ada template SOC yang terdeteksi dalam file. Periksa file Excel Anda.', 'error');
            return;
        }
        
        // Sort by confidence descending
        sheetDetections.sort((a,b) => b.confidence - a.confidence);
        
        // If multiple sheets detected, show selector
        if(sheetDetections.length > 1){
            showSheetSelector(sheetDetections);
        }else{
            // Use single detected sheet
            const best = sheetDetections[0];
            await processData(best.data, best.template, best.headers);
        }
    };
    reader.readAsBinaryString(file);
}

function showSheetSelector(detections){
    let html = '<p class="mb-1">File terpilih: <strong>' + selectedFile.name + '</strong></p>';
    html += '<div class="card mb-1" style="border: 2px solid var(--accent);">';
    html += '<h4>Beberapa Sheet Terdeteksi - Pilih Sheet:</h4>';
    html += '<div id="selector-container" style="display: flex; gap: 0.5rem; flex-wrap: wrap;">';
    html += '</div></div>';
    setHTML('file-info', html);
    
    const container = $('selector-container');
    detections.forEach(det => {
        const btn = document.createElement('button');
        btn.className = 'btn-secondary sheet-selector-btn';
        btn.textContent = `${det.sheetName} (${det.template}, ${(det.confidence*100).toFixed(0)}%)`;
        btn.addEventListener('click', () => selectSheet(det.sheetName));
        container.appendChild(btn);
    });
    
    hide($('preview-section'));
    hide($('confirm-section'));
}

async function selectSheet(sheetName){
    if(!allSheetData || !allSheetData[sheetName]){
        showToast('Sheet tidak ditemukan di dalam memori.', 'error');
        return;
    }
    
    setHTML('file-info', '<p>File terpilih: <strong>' + selectedFile.name + '</strong> (Sheet aktif: ' + sheetName + ')</p>');
    
    const sheet = allSheetData[sheetName];
    await processData(sheet.data, sheet.template, sheet.headers);
}


async function processCSV(file){
    const reader = new FileReader();
    reader.onload = async (e)=>{
        const csvText = e.target.result;
        const lines = csvText.split('\n').map(line=> line.trim()).filter(line=> line);
        if(lines.length < 2){showToast('File CSV kosong atau hanya berisi header', 'error');return;}
        
        const header = lines[0].split(',').map(h=> h.trim().replace(/^"|"$/g, ''));
        const json = [];
        
        for(let i=1; i<lines.length; i++){
            const values = lines[i].split(',').map(v=> v.trim().replace(/^"|"$/g, ''));
            const row = {};
            header.forEach((h, idx)=> { row[h] = values[idx] || ''; });
            json.push(row);
        }
        
        if(json.length===0){showToast('Tidak ada data ditemukan dalam CSV', 'error');return;}
        await processData(json);
    };
    reader.readAsText(file);
}

async function processData(json, preDetectedTemplate, preDetectedHeaders){
    parsedRows = json;
    const headers = preDetectedHeaders || Object.keys(json[0]);
    
    // Use pre-detected template if available (from sheet selection)
    if(preDetectedTemplate){
        detectedTemplate = preDetectedTemplate;
        setHTML('detected-template', detectedTemplate);
        setHTML('detect-confidence', '100%');
    }else{
        const detectRes = await apiPost('/api/import/soc/detect', {headers});
        detectedTemplate = detectRes.template_type;
        const confidence = (detectRes.confidence*100).toFixed(0);
        setHTML('detected-template', detectedTemplate);
        setHTML('detect-confidence', confidence+"%");
    }
    
    const dateCol = headers.find(h=> /day|date/i.test(h));
    if(dateCol){
        const dates = json.map(r=> new Date(r[dateCol])).filter(d=> !isNaN(d));
        if(dates.length > 0){
            const min = new Date(Math.min.apply(null, dates));
            const max = new Date(Math.max.apply(null, dates));
            detectedPeriod = {start: min.toISOString().slice(0,10), end: max.toISOString().slice(0,10)};
            setHTML('detected-period', `${detectedPeriod.start} → ${detectedPeriod.end}`);
        }
    }
    
    const previewRes = await apiPost('/api/import/soc/preview', {
        data: parsedRows,
        template_type: detectedTemplate
    });
    const preview = previewRes.preview;
    const validation = previewRes.validation;
    
    const headersPreview = Object.keys(preview[0]||{});
    const rows = preview.map(r=> headersPreview.map(h=> {
        const val = r[h];
        if(val===null || val===undefined) return '';
        if(typeof val === 'object') return JSON.stringify(val);
        return String(val).substring(0, 50);
    }));
    setHTML('preview-table-container', createTable(headersPreview, rows));
    
    if(!validation.valid){
        setHTML('validation-alert', `<div class="pill pill-danger">${validation.errors.join('<br>')}</div>`);
        show($('validation-alert'));
    }else{hide($('validation-alert'));}
    
    show($('preview-section'));
    
    if(detectedPeriod){
        const existingRes = await apiPost('/api/import/soc/check-existing', {
            template_type: detectedTemplate,
            period_start: detectedPeriod.start,
            period_end: detectedPeriod.end
        });
        if(existingRes.exists){
            show($('existing-warning'));
        }else{hide($('existing-warning'));}
    }
    show($('confirm-section'));
}

$('btn-cancel-import').addEventListener('click',()=>{
    hide($('preview-section'));
    hide($('confirm-section'));
    hide($('import-result'));
    setHTML('file-info','');
    $('soc-file-input').value='';
    selectedFile=null; parsedRows=[]; detectedTemplate=null; detectedPeriod=null; allSheetData={};
});

$('btn-execute-import').addEventListener('click', async()=>{
    const cooldownKey = `soc_import_${detectedTemplate}`;
    const last = localStorage.getItem(cooldownKey);
    if(last && Date.now() - parseInt(last) < 2*60*1000){
        const remaining = Math.ceil((2*60*1000 - (Date.now()-parseInt(last)))/1000);
        showToast(`Harap tunggu ${remaining}s sebelum mengimpor lagi tipe ini`, 'error');
        return;
    }
    
    if($('existing-warning').style.display!=='none'){
        const modal = $('replace-modal');
        modal.classList.add('active');
        const confirmBtn = $('modal-confirm');
        const cancelBtn = $('modal-cancel');
        const closeModal = ()=>{modal.classList.remove('active');};
        cancelBtn.onclick = closeModal;
        confirmBtn.onclick = async()=>{
            closeModal();
            await runImport(true);
        };
        modal.addEventListener('click', (e)=>{ if(e.target===modal) closeModal(); });
    }else{
        await runImport(false);
    }
});

async function runImport(replaceExisting){
    hide($('confirm-section'));
    setHTML('import-result','');
    show($('import-result'));
    setHTML('result-message','⏳ Mengimpor data, silakan tunggu...');
    try{
        const payload = {
            data: parsedRows,
            template_type: detectedTemplate,
            replace_existing: replaceExisting,
            period_start: detectedPeriod?.start,
            period_end: detectedPeriod?.end
        };
        const res = await apiPost('/api/import/soc/execute', payload);
        const inserted = res.inserted;
        const skipped = res.skipped;
        setHTML('result-message', `<div class="pill pill-success">Berhasil mengimpor <strong>${inserted}</strong> baris, <strong>${skipped}</strong> baris dilewati.</div>`);
        localStorage.setItem(`soc_import_${detectedTemplate}`, Date.now().toString());
    }catch(e){
        setHTML('result-message', `<div class="pill pill-danger">Import gagal: ${e.message || e}</div>`);
    }
}
