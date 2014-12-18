'''This file contains a list of IOC modules that we use at SLAC.
This is a list of module definitions.
Each line has these elements
1) The name of the module in CVS; this is the same name that eco uses and will be the name of the module folder. 
   Engineers should try to use the module name as a prefix for any tags.
   This column cannot be an empty string.
2) The name of module include definition in the configure/RELEASE. 
   For example, an IOC engineer will include the sequencer using the line SNCSEQ=$(MODULES_SITE_TOP)/seq/$(SEQ_MODULE_VERSION)
   So, this column for the sequencer will be SEQ; we'll attach the string "_MODULE_VERSION" to this column in the MODULES_STABLE_VERSION giving "SEQ_MODULE_VERSION=seq-R2-1-6_1-3"
   This column can be an empty string; these are ignored.
'''


# This list is maintained by humans. Please add items to this list in case-insensitive alphabetical order.
moduleNames = [
['a16vme', 'A16VME'],
['ADCore', ''],
['ADEdtSupport', ''],
['ADProsilica', ''],
['agilent53210a', ''],
['anc350', ''],
['areaDetector', 'AREA_DETECTOR'],
['areaDetectorSupp', ''],         
['aSubRecord', ''],               
['asyn', 'ASYN'],                 
['autosave', 'AUTOSAVE'],         
['busy', 'BUSY'],                 
['Bx9000_MBT', 'BX9000'],         
['caenADCV965', 'CAENADCV965'],   
['caenV792', 'CAENV792'],                 
['calc', 'CALC'],                     
['caPutLog', 'CAPUTLOG'],                 
['cexpsh', ''],                   
['devBusMapped', 'DEVBUSMAPPED'],             
['devGenVar', ''],                
['devlib2', ''],                  
['drvPciMcor', ''],               
['drvUioPciGen', ''],             
['drvUniverseDma', ''],                                      
['EDT_CL', ''],                                              
['epicsPing', ''],                                           
['epm2000', 'EPM2000'],                                            
['etherPSC', 'EPSC'],                                            
['ether_ip', 'ETHER_IP'],                                            
['event', 'EVENT'],                                               
['exampleCPP', ''],                              
['fcom', 'FCOM'],                               
['fcomUtil', 'FCOMUTIL'],                      
['ffmpegServer', ''],                         
['generalTime', ''],                         
['genPolySub', 'GENPOLYSUB'],                              
['genSub', 'GENSUB'],                                
['gtr', 'GTR'],                                      
['highlandLVDTV550', 'HIGHLANDLVDTV550'],            
['history', ''],                                     
['Hp53181A', 'HP53181A'],                            
['hytec8413', 'HYTEC8413'],                          
['hytecMotor8601', ''],                           
['icdTemplates', ''],                             
['ics121', ''],                                   
['ics130', ''],                                   
['InternalData', ''],                             
['iocAdmin', 'IOCADMIN'],                         
['iocCmlog', ''],                                 
['iocMon', ''],                                   
['ip231', 'IP231'],                             
['ip231-asyn', 'IP231_ASYN'],                   
['ip330', 'IP330'],                             
['ip330-asyn', 'IP330_ASYN'],                   
['ip440-asyn', 'IP440_ASYN'],                   
['ip445-asyn', 'IP445_ASYN'],                   
['ip470', 'IP470'],                             
['ipac', 'IPAC'],                               
['ipmiComm', ''],                               
['ipUnidig', 'IPUNIDIG'],                       
['laserLocking', ''],                           
['LeCroy_ENET', 'LECROY'],                      
['LLRFLibs', ''],                               
['longSubRecord', ''],                          
['mca', 'MCA'],                                 
['micro', ''],                                  
['miscUtils', 'MISCUTILS'],                     
['MKS', ''],                                    
['mksu', 'MKSU'],                               
['modbus', 'MODBUS'],                           
['ModBusTCPClnt', 'MODBUSTCPCLNT'],             
['motor', 'MOTOR'],                             
['motor59', ''],                                
['motor63', ''],                                
['motor64', ''],                                
['mps', 'MPS'],                                 
['nullhttpd', ''],                              
['pau', ''],                                    
['perfMeasure', ''],                            
['plcAdmin', 'PLCADMIN'],                   
['PSCD_Camac', 'PSCDCAMAC'],               
['pvAccessCPP', 'PVACCESS'],                
['pvaSrv', 'PVASRV'],                       
['pvCommonCPP', 'PVCOMMON'],                
['pvDataCPP', 'PVDATA'],                    
['pvIOCCPP', 'PVIOC'],                      
['pvlistServer', ''],                       
['restore', 'RESTORE'],                     
['RFControl', ''],                          
['RFControlBoard', ''],
['rtemsutils', 'RTEMSUTILS'],
['s7plc', ''],
['seq', 'SEQ'],
['sis8300', ''],
['smarActMCSMotor', ''],
['snmp', ''],
['spectrumRecord', ''],
['sqlite3', ''],
['sr620', ''],
['sscan', 'SSCAN'],
['ssi', ''],
['sSubRecord', 'SSUBRECORD'],
['std', 'STD'],
['streamdevice', 'STREAMDEVICE'],
['sub', ''],
['tds3000', 'TDS3000'],
['udpComm', 'UDPCOMM'],
['VHSx0x', 'VHSX0X'],
['vme64xSup', ''],
['vmeCardRecord', 'VME_CARD_RECORD'],
['vmic3122', ''],
['VMTG', 'VMTG'],
['vsam', 'VSAM'],
['waveAnlRecord', ''],
['waveProc', ''],
['xipIo', ''],
['XTCAVPlugin', ''],
['xy2440', 'XY2440'],
['xy2445', 'XY2445']
]
