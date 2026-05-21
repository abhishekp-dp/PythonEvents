import mysql.connector as connector
import pymysql
try:
    connection=pymysql.connect(host="172.16.7.86",
                               user="qa_write",
                               passwd="cWFfd3JpdGVfcGFzc3dvcmQ=",
                               db='dpws_qa_06')

except Exception as e:
    print(e)

x=connection.cursor()

batch_id = int(input('Enter Batch ID:'))
try:
    def transfer_data(batch_id):
        data = '''SELECT DISTINCT(pad.canister_id_id), pad.device_id_id, pad.quadrant \
                  FROM pack_analysis pa \
                           JOIN pack_analysis_details pad \
                  ON pa.id= pad.analysis_id_id \
                      JOIN canister_master cm ON cm.id= pad.canister_id_id \
                      LEFT JOIN location_master lm ON lm.id=cm.location_id_id \
                  where pa.batch_id_id=%s \
                    AND (lm.device_id_id IS NULL \
                     OR lm.device_id_id != pad.device_id_id)'''
        x.execute(data, (batch_id,))

        # Fetch all results
        can_data = x.fetchall()
        return can_data
        # for i in x.execute(data, (batch_id,), multi=True):
        #     can_data = i.fetchall()
        #     return can_data


    transfer_output = transfer_data(batch_id)


    def batch_transfer(batch_id):
        total_transfer = len(transfer_data(batch_id))
        count = 0
        for i in range(total_transfer):
            canister_id = transfer_output[i][0]
            device_id = transfer_output[i][1]
            quad = transfer_output[i][2]
            output = update(canister_id, device_id, quad)
            count = count + output
        print(f'{count} canisters tranfer')


    def empty_location(device_id, quad):
        loc = '''SELECT l.id \
                 FROM location_master l
                        JOIN device_master d ON d.id=l.device_id_id
                        left JOIN canister_master cm ON cm.location_id_id=l.id
               WHERE l.is_disabled !=1 AND l.device_id_id=%s and l.quadrant=%s AND cm.id IS null'''
        x.execute(loc, (device_id, quad))
        location = x.fetchall()
        try:
            return location[0][0]
        except:
            return location
        # for i in x.execute(loc,(device_id,quad)):
        #     location=i.fetchall()
        #     try:
        #         return location[0][0]
        #     except:
        #         return location
    def update(canister_id,device_id,quad):
        count=0
        upd2='''update canister_master c set c.location_id_id=%s where c.id=%s'''
        value1=(empty_location(device_id,quad),canister_id)
        x.execute(upd2,value1)
        connection.commit()
        count=x.rowcount+count
        return count

except Exception as e:
    print(f"Error in Transfering Canister: {e}")

batch_transfer(batch_id)