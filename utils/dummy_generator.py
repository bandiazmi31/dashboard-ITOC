import bcrypt
from datetime import datetime, timedelta
import random
from models import User, NetworkLink, SocEvent, Handover
from utils.db import Session

def seed_users():
    """Generate dummy users with different roles"""
    session = Session()
    
    users_data = [
        {"name": "Admin User", "username": "admin", "role": "Admin", "unit": "IT Operations", "job": "System Administrator", "group_shift": "Team 1"},
        {"name": "Lead Supervisor", "username": "lead1", "role": "Lead", "unit": "ITOC", "job": "Team Lead", "group_shift": "Team 1"},
        {"name": "Lead Coordinator", "username": "lead2", "role": "Lead", "unit": "ITOC", "job": "Shift Coordinator", "group_shift": "Team 2"},
        {"name": "Analyst Joko", "username": "analyst1", "role": "ITOC Analyst", "unit": "ITOC", "job": "Network Analyst", "group_shift": "Team 1"},
        {"name": "Analyst Budi", "username": "analyst2", "role": "ITOC Analyst", "unit": "ITOC", "job": "Security Analyst", "group_shift": "Team 2"},
        {"name": "Analyst Siti", "username": "analyst3", "role": "ITOC Analyst", "unit": "ITOC", "job": "Service Desk", "group_shift": "Team 3"},
        {"name": "Analyst Rudi", "username": "analyst4", "role": "ITOC Analyst", "unit": "ITOC", "job": "Network Analyst", "group_shift": "Team 4"},
        {"name": "EOS Jakarta", "username": "eos1", "role": "EOS Branch", "unit": "Jakarta Branch", "job": "Branch IT", "group_shift": None},
        {"name": "EOS Surabaya", "username": "eos2", "role": "EOS Branch", "unit": "Surabaya Branch", "job": "Branch IT", "group_shift": None},
        {"name": "Manager IT", "username": "manager", "role": "Manajemen", "unit": "IT Management", "job": "IT Manager", "group_shift": None}
    ]
    
    try:
        for user_data in users_data:
            password_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
            user = User(
                name=user_data["name"],
                username=user_data["username"],
                password_hash=password_hash,
                role=user_data["role"],
                unit=user_data["unit"],
                job=user_data["job"],
                group_shift=user_data["group_shift"]
            )
            session.add(user)
        
        session.commit()
        print(f"✓ Seeded {len(users_data)} users")
        
    except Exception as e:
        session.rollback()
        print(f"✗ User seed error: {e}")
    finally:
        session.close()

def seed_noc_links():
    """Generate dummy network links"""
    session = Session()
    
    locations = ["Jakarta", "Surabaya", "Bandung", "Semarang", "Medan"]
    isps = ["Telkom", "Biznet", "XL Axiata", "Indosat", "MyRepublic"]
    devices = ["Router Cisco ASR1000", "Router Juniper MX", "Firewall Fortinet", "Switch Core"]
    
    links_data = []
    for i in range(20):
        location = random.choice(locations)
        isp = random.choice(isps)
        uptime_pct = random.uniform(95.0, 99.9)
        total_minutes = 30 * 24 * 60
        up_time = int(total_minutes * uptime_pct / 100)
        down_time = total_minutes - up_time
        
        links_data.append(NetworkLink(
            sensor_name=f"{location}-{isp}-{i+1:03d}",
            device=random.choice(devices),
            location=location,
            isp=isp,
            target_sla=99.5,
            up_time=up_time,
            down_time=down_time,
            avg_traffic=round(random.uniform(10.0, 500.0), 2),
            volume=round(random.uniform(1.0, 50.0), 2)
        ))
    
    try:
        session.bulk_save_objects(links_data)
        session.commit()
        print(f"✓ Seeded {len(links_data)} network links")
    except Exception as e:
        session.rollback()
        print(f"✗ Network links seed error: {e}")
    finally:
        session.close()

def seed_soc_events():
    """Generate dummy SOC events"""
    session = Session()
    
    threats = [
        ("Malware Detection", "Critical"),
        ("Phishing Attempt", "High"),
        ("Brute Force Attack", "High"),
        ("SQL Injection", "Critical"),
        ("DDoS Attack", "High"),
        ("Unauthorized Access", "Medium"),
        ("Port Scan", "Low"),
        ("Suspicious Traffic", "Medium"),
        ("Data Exfiltration", "Critical"),
        ("Policy Violation", "Low")
    ]
    
    actions = ["Blocked", "Quarantined", "Alerted", "Logged"]
    categories = ["Malware", "Network Attack", "Web Attack", "Policy", "Intrusion"]
    
    events_data = []
    for i in range(300):
        days_ago = random.randint(0, 13)
        event_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        threat_name, severity = random.choice(threats)
        
        events_data.append(SocEvent(
            date=event_date,
            threat_name=threat_name,
            category=random.choice(categories),
            action=random.choice(actions),
            severity=severity,
            source_ip=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            destination_ip=f"203.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        ))
    
    try:
        session.bulk_save_objects(events_data)
        session.commit()
        print(f"✓ Seeded {len(events_data)} SOC events")
    except Exception as e:
        session.rollback()
        print(f"✗ SOC events seed error: {e}")
    finally:
        session.close()

def seed_handovers():
    """Generate dummy handover notes"""
    session = Session()
    
    admin_user = session.query(User).filter_by(username="admin").first()
    if not admin_user:
        print("✗ Admin user not found, run seed_users first")
        session.close()
        return
    
    sites = ["Jakarta DC", "Surabaya Branch", "Bandung Office", "NOC Center", "SOC Room"]
    shifts = ["Pagi", "Sore", "Malam"]
    priorities = ["Normal", "Tinggi"]
    
    handover_texts = [
        "Link Telkom Jakarta mengalami intermittent, sudah koordinasi dengan ISP",
        "Perlu monitoring server DB01, CPU usage tinggi sejak pukul 14:00",
        "Firewall rule baru sudah diapply, monitoring traffic anomaly",
        "User melaporkan akses lambat ke aplikasi ERP, sedang investigasi",
        "Backup harian berhasil, verifikasi restore point sudah OK",
        "Tiket #12345 masih open, menunggu approval user untuk maintenance",
        "SOC detected suspicious traffic dari IP 192.168.10.50, sudah diblock",
        "Link backup Biznet Surabaya standby, primary link normal",
        "Perlu eskalasi ke vendor untuk router issue di Bandung",
        "Monitoring sistem normal, tidak ada insiden major shift ini"
    ]
    
    handovers_data = []
    for i in range(15):
        days_ago = random.randint(0, 3)
        handover_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        handovers_data.append(Handover(
            text=random.choice(handover_texts),
            site=random.choice(sites),
            priority=random.choice(priorities),
            date=handover_date,
            shift=random.choice(shifts),
            open=random.choice([True, False]),
            created_by=admin_user.id
        ))
    
    try:
        session.bulk_save_objects(handovers_data)
        session.commit()
        print(f"✓ Seeded {len(handovers_data)} handovers")
    except Exception as e:
        session.rollback()
        print(f"✗ Handovers seed error: {e}")
    finally:
        session.close()

def seed_all():
    """Run all seed functions"""
    print("Starting database seed...")
    seed_users()
    seed_noc_links()
    seed_soc_events()
    seed_handovers()
    print("✓ Database seed completed")
