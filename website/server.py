from flask import Flask, render_template, request
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import openai 
from openai import OpenAI
import json
import os
client = OpenAI(
  api_key='null', 
)
import sys
import hashlib
from datetime import datetime
import logging

from dotenv import load_dotenv

from faker import Faker

fake = Faker("en_US")
import faker_edu
from faker_food import FoodProvider

fake.add_provider(faker_edu.Provider)
fake.add_provider(FoodProvider)


from ipwhois import IPWhois
from user_agent_info import parse_user_agent

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')

Base = declarative_base()

DB_USER = os.environ.get("DB_USER", "null")
DB_PASS = os.environ.get("DB_PASS", "null")
SCRAPER_VERSION = 1



if os.environ.get("PORT"):  # using Cloud Run online
    DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@/"
        f"scraper{SCRAPER_VERSION}-db?host=/cloudsql/scraper1-proj:us-central1:template-db"
    )
else:  # using Cloud SQL Auth Proxy locally
    DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@localhost:5432/scraper{SCRAPER_VERSION}-db"
    )

engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# old local db
# engine = create_engine('sqlite:///database.db')
# Session = sessionmaker(bind=engine)

class UserAgent(Base):
    __tablename__ = 'new_agents_vars'
    
    id = Column(Integer, primary_key=True)
    browser_family = Column(String, unique=False)
    user_agent = Column(String, unique=False)
    view_count = Column(Integer, unique=False)
    var1=Column(String, unique=False)
    var2=Column(String, unique=False)
    var3=Column(String, unique=False)
    var4=Column(String, unique=False)
    var5=Column(String, unique=False)
    var6=Column(String, unique=False)
    var7=Column(String, unique=False)
    var8=Column(String, unique=False)
    var9=Column(String, unique=False)
    var10=Column(String, unique=False)
    asn = Column(String, unique=False)
    hashed_ip = Column(String, unique=False)
    last_visited = Column(DateTime, unique=False)
    ip_netaddr = Column(String, unique=False) #ip until last segment

class Visits(Base):
    __tablename__ = 'new_visits'
    id = Column(Integer, primary_key=True)
    browser_family = Column(String, unique=False)
    user_agent = Column(String, unique=False)
    browser_version = Column(String, unique=False)
    os_family = Column(String, unique=False)
    os_version = Column(String, unique=False)
    device_family = Column(String, unique=False)
    is_mobile = Column(String, unique=False)
    is_tablet = Column(String, unique=False)
    is_pc = Column(String, unique=False)
    asn = Column(String, unique=False)
    ip_netaddr = Column(String, unique=False)
    hashed_ip = Column(String, unique=False)
    timestamp = Column(DateTime, default=datetime.utcnow, unique=False)

Base.metadata.create_all(engine)

def gen_vars(var1: str = "last_name()", 
             var2: str = "city()", 
             var3: str = "date_of_birth(minimum_age=20, maximum_age=85).year", 
             var4: str = "city()", 
             var5: str = "institution_name()", 
             var6: str = "city()",
             var7: str = "last_name()",
             var8: str = "last_name()",
             var9: str = "last_name()",
             var10: str = "last_name()"):

    #not the best practice, but works for our case
    fake_data = [
        str(eval(var1)),
        str(eval(var2)),
        str(eval(var3)),
        str(eval(var4)),
        str(eval(var5)),
        str(eval(var6)),
        str(eval(var7)),
        str(eval(var8)),
        str(eval(var9)),
        str(eval(var10)),
    ]

    print(fake_data)

    return fake_data

def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        # sometimes this is a list of IPs, using the first
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

def set_vars(session, max_attempts=10000):
    with open(f"varLists/scraper{SCRAPER_VERSION}.txt", 'r') as file:
        var_list = [line.strip() for line in file.readlines()[:10]]

    for i in range(max_attempts):
        vars = gen_vars(*var_list)
        exists = session.query(UserAgent).filter_by(
            var1=vars[0], var2=vars[1], var3=vars[2], var4=vars[3], var5=vars[4],
            var6=vars[5], var7=vars[6], var8=vars[7], var9=vars[8], var10=vars[9]
        ).first()
        if not exists:
            break
        
        for var_idx in range(10):
            # regen only this var
            new_var = str(eval(var_list[var_idx]))
            vars[var_idx] = new_var
            
            exists = session.query(UserAgent).filter_by(
                var1=vars[0], var2=vars[1], var3=vars[2], var4=vars[3], var5=vars[4],
                var6=vars[5], var7=vars[6], var8=vars[7], var9=vars[8], var10=vars[9]
            ).first()
            if not exists:
                break
    else:
        logging.warning("Warning: Some vars may not be unique in this generation.")
        vars = gen_vars(*var_list)
    return vars

def update_page(session,genmode,full_ua = False):
    user_agent = request.headers.get('User-Agent')
    client_ip = get_client_ip()
    asn = None
    hashed_ip = hashlib.sha256(client_ip.encode()).hexdigest() if client_ip else None
    ip_netaddr = None
    if client_ip:
        if ':' in client_ip:  # IPv6
            ip_netaddr = ':'.join(client_ip.split(':')[:-1])
        else:  # IPv4
            ip_netaddr = '.'.join(client_ip.split('.')[:-1])
    try:
        obj = IPWhois(client_ip)
        res = obj.lookup_rdap()
        asn = res.get('asn')
        print(f"ASN: {asn}")
    except Exception as e:
        print(f"ASN Error: {e}")


    # Parse user agent
    browser_family = user_agent
    browser_version = None
    os_family = None
    os_version = None
    device_family = None
    is_mobile = None
    is_tablet = None
    is_pc = None
    try:
        ua_info = parse_user_agent(user_agent, session_id=None)
        browser_family = ua_info.get('browser_family')
        browser_version = ua_info.get('browser_version')
        os_family = ua_info.get('os_family')
        os_version = ua_info.get('os_version')
        device_family = ua_info.get('device_family')
        is_mobile = str(ua_info.get('is_mobile'))
        is_tablet = str(ua_info.get('is_tablet'))
        is_pc = str(ua_info.get('is_pc'))
        if not browser_family:
            browser_family = user_agent
    except Exception as e:
        logging.warning(f"Useragent Error: {e}")
        

    visit_entry = Visits(
        browser_family=browser_family,
        user_agent=user_agent,
        browser_version=browser_version,
        os_family=os_family,
        os_version=os_version,
        device_family=device_family,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        is_pc=is_pc,
        asn=asn,
        ip_netaddr=ip_netaddr,
        hashed_ip=hashed_ip
    )
    session.add(visit_entry)
    session.commit()

    
    # if genmode: full_ua = True
    # if not full_ua: user_agent = user_agent.split('/')[0]

    # Same user_agent and asn
    exactEntry = session.query(UserAgent).filter_by(user_agent=user_agent, asn=asn).first()

    # Same user_agent and asn
    if exactEntry:
        seen_before = True
        var1 = exactEntry.var1
        var2 = exactEntry.var2
        var3 = exactEntry.var3
        var4 = exactEntry.var4
        var5 = exactEntry.var5
        var6 = exactEntry.var6
        var7 = exactEntry.var7
        var8 = exactEntry.var8
        var9 = exactEntry.var9
        var10 = exactEntry.var10
        exactEntry.view_count += 1
        if asn:
            exactEntry.asn = asn
        if hashed_ip:
            exactEntry.hashed_ip = hashed_ip
        if ip_netaddr:
            exactEntry.ip_netaddr = ip_netaddr
        exactEntry.last_visited = datetime.utcnow()
        session.commit()
        #
        # new_entry = UserAgent(
        #     browser_family=browser_family,
        #     user_agent=user_agent,
        #     view_count=1,
        #     var1=var1,
        #     var2=var2,
        #     var3=var3,
        #     var4=var4,
        #     var5=var5,
        #     var6=var6,
        #     var7=var7,
        #     var8=var8,
        #     var9=var9,
        #     var10=var10,
        #     asn=asn,
        #     hashed_ip=hashed_ip,
        #     ip_netaddr=ip_netaddr,
        #     last_visited=datetime.utcnow()
        # )
        # session.add(new_entry)
        # session.commit()
    else:
        # New user_agent and asn
        seen_before = False
        if genmode:
            var1, var2, var3, var4, var5, var6, var7, var8, var9, var10 = set_vars(session=session)
            new_entry = UserAgent(
                browser_family=browser_family,
                user_agent=user_agent,
                view_count=1,
                var1=var1,
                var2=var2,
                var3=var3,
                var4=var4,
                var5=var5,
                var6=var6,
                var7=var7,
                var8=var8,
                var9=var9,
                var10=var10,
                asn=asn,
                hashed_ip=hashed_ip,
                ip_netaddr=ip_netaddr,
                last_visited=datetime.utcnow()
            )
            session.add(new_entry)
            session.commit()
        else:
            #Display to all useragents not accounted for when not in genmode
            var1 = "Null"
            var2 = "Null"
            var3 = "Null"
            var4 = "Null"
            var5 = "Null"
            var6 = "Null"
            var7 = "Null"
            var8 = "Null"
            var9 = "Null"
            var10 = "Null"

    session.close()

    return render_template(f"scraper{SCRAPER_VERSION}.html", user_agent=user_agent, seen_before = seen_before, var1 = var1, var2 = var2, var3 = var3, var4 = var4, var5 = var5, var6 = var6, var7 = var7, var8 = var8, var9 = var9, var10 = var10)

@app.route('/', methods=['GET'])
def index():
    genmode = True
    if len(sys.argv) >= 2 and sys.argv[1] == "nogen":
        genmode = False

    print(f"Genmode: {genmode}")

    session = Session()

    return update_page(session,genmode)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False)