import time, os, zipfile

lastday = int(time.time()) - 86400
lastday_date = time.localtime(lastday)
lastday_date_name = time.strftime("%y%m%d",lastday_date)
now_date_name = time.strftime("%y%m%d")

########### 处理今天和昨天的LISTVTOC文件 #####################
print("处理LISTVTOC文件..")
try:
    with open("LISTVTOC.D%s" %now_date_name,encoding='ISO-8859-1') as f_today:
        rpt_lines = f_today.readlines()

except UnicodeDecodeError as e:
    print(repr(e))
    print(str(traceback.format_exc()))

except FileNotFoundError:
    outfile = open("VI_CHECK.D%s" %now_date_name,'w')
    outfile.write("LISTVTOC.D%s 不存在." %now_date_name) 
    outfile.close()

else:
    for i in range(len(rpt_lines)):
        rpt_lines[i] = rpt_lines[i].strip().split()
        
    ########### Retrive VOLUME ###############
    volume_list       = [i[5] for i in rpt_lines if len(i)>6 and i[4]=='VOL']

    ########### Retrive the line num next to "Format 4" line ###############
    # DUMP VIEW:
    #vi_line_num_list  = [i+1 for (i,x) in enumerate(rpt_lines) if len(x)>2 and x[0]=='FORMAT' and x[1]=='4']
    # FORMAT VIEW:
    vi_line_num_list  = [i+2 for (i,x) in enumerate(rpt_lines) if len(x)>3 and x[1]=='FORMAT' and x[2]=='4']

    ########### Retrive VI,Hex to Bin ###############                
    # DUMP VIEW:                
    #vi_list_hex = [rpt_lines[x][0][28:30] for x in vi_line_num_list]
    # FORMAT VIEW:                
    vi_list_hex = [rpt_lines[x][0] for x in vi_line_num_list]
    
    vi_list_bin_hex = [(('{0:04b}{1:04b}'.format(int(vh[0],16),int(vh[1],16))),vh) for vh in vi_list_hex]

    ########### Statistic on VIs ###############
    vi_set = set(vi_list_bin_hex)
    vi_list_statistic = [(vi,vi_list_bin_hex.count(vi)) for vi in vi_set]

    ########### Generate the complete list of Volume/DI pair ###############  
    out1_list = list(zip(volume_list,vi_list_bin_hex))

    ########### DIRF bit. A VTOC change is incomplete.###############  
    out2_list = [line for line in out1_list if line[1][0][-3] == '1']

    ########### Write To file ###############
    outfile = open("VI_CHECK.D%s" %now_date_name,'w')

    outfile.write("LISTVTOC.D%s 抽取结果:" %now_date_name)

    outfile.write("\n VI  bin(hex)  卷数量")
    ########### Write Statistic result #####################    
    for r in vi_list_statistic:
        outfile.write("\n %s(%s)   %s" %(r[0][0],r[0][1],r[1]))
    outfile.write("\n 总 计          %s" %len(out1_list))
    
    outfile.write('\n\n VOLUME    VI bin(hex)   SPACALL   FREEKB        %FREE  DEVCAP    FRAGINDX  DEVNUM   STORGRP')
    ########### Process LISTVTOC & SGDAY #####################    
    if len(out2_list) > 0:
        print("盘卷VI异常,正在匹配卷信息..")
        try:
            f_sg_today = open("SGDAY.D%s" %now_date_name)
        except FileNotFoundError:
            for line1 in out2_list:
                outfile.write('\n %s   %s(%s)' %(line1[0],line1[1][0],line1[1][1]))
            outfile.write("\n\nSGDAY.D%s    匹配进度:文件未找到." %now_date_name)
        else:
            for line1 in out2_list:
                outfile.write('\n %s   %s(%s)' %(line1[0],line1[1][0],line1[1][1]))
                for line_sg in f_sg_today:
                    if line1[0] in line_sg:
                        outfile.write('   %s     %s' %(line_sg[12:67],line_sg[2:10]))
                        break
                f_sg_today.seek(0)
                    
            outfile.write("\n\nSGDAY.D%s    匹配进度:已完成." %now_date_name)
            f_sg_today.close()

    else:
        outfile.write('\n 盘卷DIRF无异常.')
        outfile.write("\n\nSGDAY.D%s 匹配进度:无需匹配." %now_date_name)

    ######### Create zip file if not exist ###############
    exist = zipfile.is_zipfile("LISTVTOC.D%s.zip" %lastday_date_name)

    if not exist:
        f_zip = zipfile.ZipFile("LISTVTOC.D%s.zip" %lastday_date_name,'w',zipfile.ZIP_DEFLATED)
        
        try:
             f_zip.write("LISTVTOC.D%s" %lastday_date_name)
        except FileNotFoundError:
            f_zip.close()
            os.remove("LISTVTOC.D%s.zip" %lastday_date_name)
            outfile.write("\n\nLISTVTOC.D%s 归档进度:文件未找到." %lastday_date_name) 
        else:
            f_zip.close()
            os.remove("LISTVTOC.D%s" %lastday_date_name)
            outfile.write("\n\nLISTVTOC.D%s 归档进度:已归档." %lastday_date_name) 
    else:
        outfile.write("\n\nLISTVTOC.D%s 归档进度:归档已存在,无需再次归档." %lastday_date_name)

        
    ########### END #####################    
    outfile.write('\n\n  #VI bit pos   #bit值   #说明')
    outfile.write('\n   1(L)          1        VSE bit. Either invalid format 5 DSCBs or indexed VTOC. Previously DOS(VSE) bit. See DS4IVTOC.')
    outfile.write('\n   2             1        Index was disabled. \n   3             1        Extended free-space management flag. When DS4EFVLD is on, the volume is in OSVTOC format with valid free space information in the format-7 DSCBs. See also DS4EFLVL and DS4EFPTR.')
    outfile.write('\n   4             1        VSE stacked pack. \n   5             1        VSE converted VTOC. \n  *6             1        DIRF bit. A VTOC change is incomplete.')
    outfile.write('\n   7             1        DIRF reclaimed. \n   8(R)          1        Volume uses an indexed VTOC.')  
    outfile.write('\n\n Please reference DFSMSdfp Advanced Service for more info about VTOC Indicator.')
    outfile.write('\n https://www.ibm.com/support/knowledgecenter/ja/SSLTBW_2.3.0/com.ibm.zos.v2r3.idas300/s3027.htm')
    outfile.close()

print("处理完成,请查看VI_CHECK文件.")

###Known bugs
#1 Abnormal volume/DI pair is not shown while no matched record found in SGDAY. fixed
