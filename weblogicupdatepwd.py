import sys

dsPassword1 = sys.argv[1]
dsPassword2 = sys.argv[2]
dsPassword3 = sys.argv[3]
dsPassword4 = sys.argv[4]
dsPassword5 = sys.argv[5]
dsPassword6 = sys.argv[6]
admin_username = sys.argv[7]
admin_password = sys.argv[8]
admin_hostname = sys.argv[9]


dsName1 = "hpdb_hrdb"
dsName2 = "hrdb_seeker"
dsName3 = "hrdb_sysadm"
dsName4 = "hrdb_wlsession"
dsName5 = "pndb_seeker"

if "slm" in admin_hostname:
    dsName6 = "pidb_tpi"
else:
    dsName6 = "tpi_db"

def updatePwd(uDSName, uDBPASS):
    cd('/JDBCSystemResources/'+uDSName+'/JDBCResource/' + uDSName+'/JDBCDriverParams/'+uDSName)
    cmo.setPassword(uDBPASS)
    print(" Password has been Changed for DataSource: ", uDSName)
    return

connect(admin_username, admin_password, 't3://'+ admin_hostname +':7001')

cd('Servers/AdminServer')
edit()
startEdit()
cd('JDBCSystemResources')
allDS=cmo.getJDBCSystemResources()

for tmpDS in allDS:
  dsName=tmpDS.getName();
  if dsName == dsName1:
      updatePwd(dsName,dsPassword1)
  elif dsName == dsName2:
      updatePwd(dsName, dsPassword2)
  elif dsName == dsName3:
      updatePwd(dsName, dsPassword3)
  elif dsName == dsName4:
      updatePwd(dsName, dsPassword4)
  elif dsName == dsName5:
      updatePwd(dsName, dsPassword5)
  elif dsName == dsName6:
      updatePwd(dsName, dsPassword6)
  else:
      print('Unable to find the DataSource')

save()
activate()
