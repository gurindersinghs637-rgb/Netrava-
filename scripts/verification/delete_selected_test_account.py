"""Explicitly approved deletion of one empty test account; refuse scope changes."""
import httpx
from backend.app.core.config import settings

TARGET='preamgills232@gmail.com'
UID='f7c67b0b-a1b3-4cf9-ae9e-9180a7377f7a'
WORKSPACE='b84915fc-143d-4591-bcd4-25203f164299'
BASE=settings.SUPABASE_URL.rstrip('/')
HEADERS={'apikey':settings.SUPABASE_SERVICE_ROLE_KEY,'Authorization':'Bearer '+settings.SUPABASE_SERVICE_ROLE_KEY}

def main():
    with httpx.Client(headers=HEADERS,timeout=20) as c:
        def rows(table,filters):
            r=c.get(BASE+'/rest/v1/'+table,params={'select':'*',**filters});r.raise_for_status();return r.json()
        def empty(table,filters):
            r=c.get(BASE+'/rest/v1/'+table,params={'select':'id','limit':'1',**filters});r.raise_for_status()
            if r.json():raise RuntimeError('Deletion refused: related records in '+table)
        r=c.get(BASE+'/auth/v1/admin/users/'+UID);r.raise_for_status()
        if r.json().get('email','').lower()!=TARGET:raise RuntimeError('Auth identity changed')
        profiles=rows('user_profiles',{'clinic_id':'eq.'+WORKSPACE})
        if len(profiles)!=1 or profiles[0]['id']!=UID or profiles[0]['role']!='technician':
            raise RuntimeError('Deletion refused: workspace membership changed')
        clinics=rows('clinics',{'id':'eq.'+WORKSPACE})
        if len(clinics)!=1 or clinics[0]['clinic_name']!='Personal screening workspace':raise RuntimeError('Workspace changed')
        for table,column,value in [
            ('patients','clinic_id',WORKSPACE),('screenings','clinic_id',WORKSPACE),('audit_logs','clinic_id',WORKSPACE),
            ('patients','created_by',UID),('screenings','technician_id',UID),('retinal_images','uploaded_by',UID),
            ('reports','reviewer_id',UID),('audit_logs','user_id',UID)]:
            empty(table,{column:'eq.'+value})
        for bucket in ['fundus-images','gradcam-heatmaps','clinical-reports']:
            r=c.post(BASE+'/storage/v1/object/list/'+bucket,json={'prefix':WORKSPACE+'/','limit':1,'offset':0});r.raise_for_status()
            if r.json():raise RuntimeError('Deletion refused: workspace has stored objects')
        # Preserve baseline for unrelated account/profile and clinical table counts.
        important_id='2ca753d6-5ad9-4dec-a70f-5a04c7c9b6b1'
        important_before=rows('user_profiles',{'id':'eq.'+important_id})
        def count(table):
            r=c.get(BASE+'/rest/v1/'+table,params={'select':'id','limit':'0'},headers={'Prefer':'count=exact'});r.raise_for_status()
            return r.headers['content-range'].split('/')[-1]
        counts_before={t:count(t) for t in ['patients','screenings','retinal_images','predictions','reports','audit_logs']}
        # Deactivate first, so this account cannot initiate new authenticated work.
        r=c.patch(BASE+'/rest/v1/user_profiles',params={'id':'eq.'+UID,'clinic_id':'eq.'+WORKSPACE,'role':'eq.technician'},json={'is_active':False},headers={'Prefer':'return=representation'});r.raise_for_status()
        if len(r.json())!=1:raise RuntimeError('Conditional deactivation failed')
        # Hard-delete Auth identity, then remove only the matching profile and workspace.
        r=c.request('DELETE',BASE+'/auth/v1/admin/users/'+UID,json={'should_soft_delete':False})
        r.raise_for_status()
        r=c.delete(BASE+'/rest/v1/user_profiles',params={'id':'eq.'+UID,'clinic_id':'eq.'+WORKSPACE});r.raise_for_status()
        r=c.delete(BASE+'/rest/v1/clinics',params={'id':'eq.'+WORKSPACE});r.raise_for_status()
        assert not rows('user_profiles',{'id':'eq.'+UID})
        assert not rows('clinics',{'id':'eq.'+WORKSPACE})
        r=c.get(BASE+'/auth/v1/admin/users/'+UID)
        assert r.status_code==404, 'Auth deletion could not be verified'
        page=1
        while True:
            r=c.get(BASE+'/auth/v1/admin/users',params={'page':page,'per_page':100});r.raise_for_status()
            users=r.json().get('users',[])
            assert not any(u.get('email','').lower()==TARGET for u in users)
            if len(users)<100:break
            page+=1
        assert rows('user_profiles',{'id':'eq.'+important_id})==important_before
        r=c.get(BASE+'/auth/v1/admin/users/'+important_id);r.raise_for_status()
        assert r.json()['email']=='gurindersinghs331@gmail.com'
        assert {t:count(t) for t in counts_before}==counts_before
        print('Verified: selected Auth account, profile and empty workspace deleted.')
        print('Verified: email absent from Auth; administrator account/profile preserved; clinical record counts unchanged.')

if __name__=='__main__':main()
