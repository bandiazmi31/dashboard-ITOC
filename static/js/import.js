function parseExcelFile(file, sheetType, callback) {
    const reader = new FileReader();
    
    reader.onload = (e) => {
        try {
            const data = e.target.result;
            const workbook = XLSX.read(data, { type: 'binary' });
            const sheetName = workbook.SheetNames[0];
            const sheet = workbook.Sheets[sheetName];
            const jsonData = XLSX.utils.sheet_to_json(sheet);
            
            const mappedData = jsonData.map(row => mapExcelColumns(row, sheetType));
            callback(null, mappedData);
        } catch (err) {
            callback(err, null);
        }
    };
    
    reader.onerror = () => {
        callback(new Error('Failed to read file'), null);
    };
    
    reader.readAsBinaryString(file);
}

function mapExcelColumns(row, sheetType) {
    if (sheetType === 'tickets') {
        return {
            req_id: row['Request ID'] || row['ID'],
            mode: row['Mode'] || 'Web',
            requester: row['Requester'],
            category: row['Category'],
            subcategory: row['Subcategory'],
            subject: row['Subject'],
            technician: row['Technician'],
            sla_name: row['SLA'],
            priority: row['Priority'],
            created_time: row['Created Time'],
            resolved_time: row['Resolved Time'],
            status: row['Status']
        };
    } else if (sheetType === 'links') {
        return {
            sensor_name: row['Sensor Name'],
            device: row['Device'],
            location: row['Location'],
            isp: row['ISP'],
            target_sla: row['Target SLA'],
            up_time: row['Up Time'],
            down_time: row['Down Time'],
            avg_traffic: row['Avg Traffic'],
            volume: row['Volume']
        };
    } else if (sheetType === 'soc') {
        return {
            date: row['Date'],
            threat_name: row['Threat Name'],
            category: row['Category'],
            action: row['Action'],
            severity: row['Severity'],
            source_ip: row['Source IP'],
            destination_ip: row['Destination IP']
        };
    }
    
    return row;
}

async function uploadExcelData(sheetType, data) {
    try {
        showToast('Mengupload data...', 'info');
        const endpoint = `/api/import/${sheetType}`;
        await apiPost(endpoint, { data });
        showToast(`Berhasil mengupload ${data.length} record`, 'success');
    } catch (err) {
        showToast('Upload gagal: ' + err.message, 'error');
    }
}
