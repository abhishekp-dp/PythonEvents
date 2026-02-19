import pymysql

try:
    connection = pymysql.connect(
        host="172.16.7.86",
        user="qa_write",
        passwd="cWFfd3JpdGVfcGFzc3dvcmQ=",
        db="dpws_qa_04",
        autocommit=False
    )
except Exception as e:
    print("DB Connection Error:", e)
    exit()

cursor = connection.cursor()
batch_id = int(input("Enter Batch ID: "))

try:
    def revert_batch(batch_id):
        queries = [

            "SET SQL_SAFE_UPDATES=0",
            "SET FOREIGN_KEY_CHECKS=0",
            "SET SESSION group_concat_max_len = 1000000",

            """DELETE FROM pack_analysis_details 
               WHERE analysis_id_id IN 
               (SELECT id FROM pack_analysis WHERE batch_id_id=%s)""",

            "DELETE FROM pack_analysis WHERE batch_id_id=%s",

            "DELETE FROM reserved_canister WHERE batch_id_id=%s",

            """DELETE FROM canister_transfer_history_comment
               WHERE canister_tx_history_id_id IN (
                   SELECT id FROM canister_transfer_cycle_history
                   WHERE canister_transfer_id_id IN (
                       SELECT id FROM canister_transfers WHERE batch_id_id=%s
                   )
               )""",

            """DELETE FROM canister_transfer_cycle_history
               WHERE canister_transfer_id_id IN (
                   SELECT id FROM canister_transfers WHERE batch_id_id=%s
               )""",

            "DELETE FROM canister_transfers WHERE batch_id_id=%s",

            "DELETE FROM canister_tx_meta WHERE batch_id_id=%s",

            "UPDATE batch_master SET status_id=34 WHERE id=%s",

            """UPDATE pack_details 
               SET pack_status_id=2 
               WHERE pack_status_id IN (2,3,5,7,162,8,45,367)
               AND batch_id_id=%s""",

            """DELETE FROM mfd_cycle_history_comment
               WHERE cycle_history_id_id IN (
                   SELECT id FROM mfd_cycle_history
                   WHERE analysis_id_id IN (
                       SELECT id FROM mfd_analysis WHERE batch_id_id=%s
                   )
               )""",

            """DELETE FROM mfd_cycle_history
               WHERE analysis_id_id IN (
                   SELECT id FROM mfd_analysis WHERE batch_id_id=%s
               )""",

            """DELETE FROM mfd_analysis_details
               WHERE analysis_id_id IN (
                   SELECT id FROM mfd_analysis WHERE batch_id_id=%s
               )""",

            "DELETE FROM mfd_analysis WHERE batch_id_id=%s",

            "UPDATE batch_master SET sequence_no=0 WHERE id=%s",

            """DELETE FROM pack_queue
               WHERE pack_id_id IN (
                   SELECT id FROM pack_details WHERE batch_id_id=%s
               )""",

            """DELETE FROM drug_tracker
               WHERE pack_id_id IN (
                   SELECT id FROM pack_details WHERE batch_id_id=%s
               )""",

            """DELETE FROM slot_transaction
               WHERE pack_id_id IN (
                   SELECT id FROM pack_details WHERE batch_id_id=%s
               )""",

            "UPDATE pack_details SET car_id=NULL WHERE batch_id_id=%s",

            """DELETE p
               FROM pack_user_map p
               JOIN pack_details pd ON pd.id=p.pack_id_id
               WHERE pd.batch_id_id=%s"""
        ]

        for q in queries:
            if "%s" in q:
                cursor.execute(q, (batch_id,))
            else:
                cursor.execute(q)

        connection.commit()
        print(f"Batch {batch_id} reverted successfully ✅")

    revert_batch(batch_id)

except Exception as e:
    connection.rollback()
    print("Error during batch revert ❌:", e)

finally:
    cursor.close()
    connection.close()


