'''
Created on Nov 30, 2016

@author: Venkatesh
'''
import logging
from pyth.cms.dao.SourceTargetConnector import DbConnector, FileConnector,\
    SolrConnector
from pyth.cms.model.Entities import Claimant, CptCode, BillLine
from pyth.cms.properties import appProperties as appProp
from pyth.cms.dao.EntityDAO import FacilityProviderDAO, RenderingProviderDAO,\
    ReferringProviderDAO, BilledCptCodeDAO, PaidCptCodeDAO, BillingProviderDAO
from pysolr import SolrError


module_logger = logging.getLogger('pyth.cms.dao.TestData')
module_logger.addHandler(logging.StreamHandler())
module_logger.setLevel(logging.INFO)
#module_logger.setLevel(logging.INFO)

def printdict(dictitem,d2):
    keys = dictitem.keys()
    for key in keys:
        if isinstance(dictitem[key], dict):
            printdict(dictitem[key],d2)
        elif isinstance(dictitem[key],CptCode):
            d2[key]=dictitem[key].__dict__
        else:
            d2[key]=dictitem[key]


def prepareData(appProp):
    
    billprovider = BillingProviderDAO()
    billingproviderlist = billprovider.getBillProviders()
    billproviderslen =len(billingproviderlist)
    
    facilityprovider = FacilityProviderDAO()
    facilitylist = facilityprovider.getProviders()
    facilitylen = len(facilitylist)
    
    renderingprovider = RenderingProviderDAO()
    renderinglist = renderingprovider.getProviders()
    renderinglen = len(renderinglist)
    
    referringprovider = ReferringProviderDAO()
    referringlist = referringprovider.getProviders()
    referringlen = len(referringlist)
    
    claimant = Claimant()
    cllist = claimant.getClaimants()
    claimantslen = len(cllist)
        
    billedCptcodes = BilledCptCodeDAO()
    billedcpts = billedCptcodes.getCodes()
    billedcptlen = len(billedcpts) 
    
    paidCptcodes = PaidCptCodeDAO()
    paidcpts = paidCptcodes.getCodes()
    paidcptlen = len(paidcpts) 
      
    '''
    Generate a billline and then use this array to build bills which in turn will generate the cclaims
    '''
    import random
    billlines=[]
    
    for clmt in range(1, random.randint(2,appProp.MAX_CLAIMANT_COUNT)):
        for claim in range(1, random.randint(1,appProp.MAX_CLAIM_COUNT)):
            for bills in range(1, random.randint(2,appProp.MAX_BILLS_COUNT)):
                
                for lineno in range(1, random.randint(1,appProp.MAX_LINES_PER_BILL)):
                    billlines.append(
                        BillLine(cllist[clmt % claimantslen],   #Claimant 
                                 appProp.CLAIM_PREFIX + str(claim).ljust(3,'0'), # claim number
                                 appProp.BILL_PREFIX+appProp.CLAIM_PREFIX+str(bills).ljust(6,'0'), # Bill Number
                                 billingproviderlist[bills  % billproviderslen], # Billing Provider
                                 renderinglist[(bills) % renderinglen], # Rendering Provider
                                 facilitylist[(bills)% facilitylen], #facility provider
                                 lineno, 
                                 billedcpts[lineno % billedcptlen], # Billed copt
                                 paidcpts[lineno % paidcptlen], # paid cpt
                        ))
 
    return billlines                
            
if __name__ == '__main__':
    
    billlines = prepareData(appProp)
#    c = CMSSolr()
#   for 
#    c.insertDocument()
    for sink in appProp.target_sink.split(" "):
        if sink == 'file':
            module_logger.info('Starting with File Loader')
            fileconnector = FileConnector(appProp)
            fileconnector.writehdr(billlines[0].printHeaderLabels())
            for bill_file in billlines:
                fileconnector.writelines(str(bill_file)) 
            fileconnector.close()
            module_logger.info('Completed writing into the file')  
        
        elif sink=='solr':
            module_logger.info('Starting to load into Solr')
            try : 
                dictArr=[]
                solrconn = SolrConnector(appProp)
                for bill_file in billlines:
                    dictArr.append(bill_file.solrFormat())
                solrconn.insertDocument(dictArr) 
                module_logger.info('Completed writing into Solr Collection')   
            except SolrError:
                module_logger.error('Solr connection not available. Check if Solr is up and running')
                
        elif sink=='database':
            module_logger.info('Starting to load into Db')
            db = DbConnector(appProp)
            for bill in billlines:
                db.insertRecord(bill) 
            module_logger.info('Completed write to DB')