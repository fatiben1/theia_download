import json
import time
import os, os.path, optparse,sys
from datetime import date

###########################################################################
class OptionParser (optparse.OptionParser):
 
    def check_required (self, opt):
      option = self.get_option(opt)
 
      # Assumes the option's 'default' is set to None!
      if getattr(self.values, option.dest) is None:
          self.error("%s option not supplied" % option)
 
###########################################################################

#==================
#parse command line
#==================
if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print '      '+sys.argv[0]+' [options]'
    print "     Aide : ", prog, " --help"
    print "        ou : ", prog, " -h"
    print "example : python %s -q 'Toulouse' -a hagolle_theia.txt -d 2015-11-01 -f 2015-12-01"%sys.argv[0]
    print "example : python %s -q 'Toulouse' -a hagolle_theia.txt -c SpotWorldHeritage -p SPOT4 -d 2005-11-01 -f 2006-12-01"%sys.argv[0]
    sys.exit(-1)
else :
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage)
  
    parser.add_option("-q","--query", dest="query", action="store", type="string", \
            help="query : example Toulouse 2013",default=None)		
    parser.add_option("-a","--auth_theia", dest="auth_theia", action="store", type="string", \
            help="Theia account and password file")
    parser.add_option("-w","--write_dir", dest="write_dir", action="store",type="string",  \
            help="Path where the products should be downloaded",default='.')
    parser.add_option("-c","--collection", dest="collection", action="store", type="choice",  \
            help="Collection within theia collections",choices=['Landsat','SpotWorldHeritage'],default='Landsat')
    parser.add_option("-n","--no_download", dest="no_download", action="store_true",  \
            help="Do not download products, just print curl command",default=False)
    parser.add_option("-d", "--start_date", dest="start_date", action="store", type="string", \
            help="start date, fmt('2015-12-22')",default=None)
    parser.add_option("-f","--end_date", dest="end_date", action="store", type="string", \
            help="end date, fmt('2015-12-23')",default=None)
    parser.add_option('-p', '--platform', type='choice', action='store', dest='platform',\
                      choices=['LANDSAT5','LANDSAT7','LANDSAT8','SPOT1','SPOT2','SPOT3','SPOT4','SPOT5'], default='LANDSAT8',  help='Satellite',)

    (options, args) = parser.parse_args()

if options.start_date!=None:    
    start_date=options.start_date
    if options.end_date!=None:
        end_date=options.end_date
    else:
        end_date=date.today().isoformat()


#====================
# read authentification file
#====================
try:
    f=file(options.auth_theia)
    (email,passwd)=f.readline().split(' ')
    if passwd.endswith('\n'):
        passwd=passwd[:-1]
    f.close()
except :
    print "error with password file"
    sys.exit(-2)
query=options.query.replace(" ","\ ")

#============================================================
# get a token to be allowed to bypass the authentification.
# The token is only valid for two hours. If your connection is slow
# or if you are downloading lots of products, it might be an issue
#=============================================================

get_token='curl -k -s -X POST --data-urlencode "ident=%s" --data-urlencode "pass=%s" https://theia.cnes.fr/services/authenticate/>token.json'%(email,passwd)

os.system(get_token)

with open('token.json') as data_file:    
    token_json = json.load(data_file)
    token=token_json["access_token"]

#====================
# search catalogue
#====================

if os.path.exists('search.json'):
    os.remove('search.json')
    
search_catalog='curl -k -o search.json https://theia.cnes.fr/resto/api/collections/%s/search.json?q=%s\&platform=%s\&startDate=%s\&completionDate=%s\&maxRecords=500'%(options.collection,query,options.platform,start_date,end_date)
print search_catalog
os.system(search_catalog)
time.sleep(10)


#====================
# Download
#====================

with open('search.json') as data_file:    
    data = json.load(data_file)

for i in range(len(data["features"])):    
    print data["features"][i]["properties"]["productIdentifier"],data["features"][i]["id"],data["features"][i]["properties"]["startDate"]
    prod=data["features"][i]["properties"]["productIdentifier"]
    feature_id=data["features"][i]["id"]
    get_product='curl -o %s.zip -k -H "Authorization: Bearer %s" https://theia.cnes.fr/resto/collections/Landsat/%s/download/?issuerId=theia'%(prod,token,feature_id)
    print get_product
    if not(options.no_download):
        os.system(get_product)

