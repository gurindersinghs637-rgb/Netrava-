"""Owner-approved one-account repair using the configured backend REST credentials."""
import asyncio
import httpx
from backend.app.core.config import settings

async def main():
    base = settings.SUPABASE_URL.rstrip('/')
    headers = {'apikey': settings.SUPABASE_SERVICE_ROLE_KEY,
               'Authorization': 'Bearer '+settings.SUPABASE_SERVICE_ROLE_KEY}
    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        matches=[]
        page=1
        while True:
            r=await client.get(base+'/auth/v1/admin/users',params={'page':page,'per_page':100})
            r.raise_for_status()
            users=r.json().get('users',[])
            matches.extend(u for u in users if u.get('email','').lower()=='preamgills232@gmail.com')
            if len(users)<100: break
            page+=1
        if len(matches)!=1: raise RuntimeError('Expected exactly one matching account')
        identity=matches[0]
        uid=identity['id']
        params={'id':'eq.'+uid,'select':'id,role,is_active,clinic_id,full_name,email,phone'}
        r=await client.get(base+'/rest/v1/user_profiles',params=params)
        r.raise_for_status()
        rows=r.json()
        if len(rows)!=1: raise RuntimeError('Expected existing profile')
        profile=rows[0]
        if profile['role']!='technician': raise RuntimeError('Non-technician refused')
        if profile.get('clinic_id'):
            print('Account already has workspace; no repair mutation performed')
        else:
            r=await client.post(base+'/rest/v1/clinics',headers={'Prefer':'return=representation'},json={'clinic_name':'Personal screening workspace','is_active':True})
            r.raise_for_status()
            workspace=r.json()[0]['id']
            try:
                r=await client.patch(base+'/rest/v1/user_profiles',params={'id':'eq.'+uid,'clinic_id':'is.null','role':'eq.technician'},headers={'Prefer':'return=representation'},json={'full_name':'Gurinder Singh','email':identity['email'],'phone':'7087655575','clinic_id':workspace,'is_active':True})
                r.raise_for_status()
                if len(r.json())!=1: raise RuntimeError('Concurrent profile change detected')
            except Exception:
                # On uncertain network outcome, retain any workspace linked by the profile.
                check=await client.get(base+'/rest/v1/user_profiles',params=params)
                check.raise_for_status()
                if check.json()[0].get('clinic_id') != workspace:
                    cleanup=await client.delete(base+'/rest/v1/clinics',params={'id':'eq.'+workspace})
                    cleanup.raise_for_status()
                raise
            print('Targeted repair applied')
        r=await client.get(base+'/rest/v1/user_profiles',params={**params,'select':'id,role,is_active,clinic_id,full_name,email,phone,clinic:clinics(id,clinic_name,is_active)'})
        r.raise_for_status()
        p=r.json()[0]
        assert p['is_active'] is True and p['role']=='technician'
        assert p['clinic_id'] and p['clinic']['id']==p['clinic_id'] and p['clinic']['is_active'] is True
        assert p['full_name']=='Gurinder Singh' and p['phone']=='7087655575' and p['email']==identity['email']
        print('Verified: active technician, active private workspace, saved name/email/phone, confirmed Auth email:',bool(identity.get('email_confirmed_at')))

if __name__=='__main__':
    asyncio.run(main())
