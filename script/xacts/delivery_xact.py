from datetime import datetime


def get_and_update_next_o_id_to_deliver(session, w_id, d_id):
    prepared = session.prepare(
        "SELECT d_next_o_id_to_deliver FROM district WHERE d_w_id = ? AND d_id = ?")
    rows = list(session.execute(prepared.bind(())))
    next_o_id_to_deliver = int(rows[0].d_next_o_id_to_deliver)

    prepared = session.prepare(
        "UPDATE district SET d_next_o_id_to_deliver = ? WHERE d_w_id = ? AND d_id = ?")
    session.execute(prepared.bind(
        (next_o_id_to_deliver + 1, int(w_id), int(d_id))))
    return next_o_id_to_deliver


def update_order(session, w_id, d_id, o_id, carrier_id):
    prepared = session.prepare(
        "UPDATE order_table SET o_carrier_id = ? WHERE o_w_id = ? AND o_d_id = ? AND o_id")
    session.execute(prepared.bind(
        ((int(carrier_id), int(w_id), int(d_id), o_id))))


def update_order_lines_and_get_total_order_amount(session, w_id, d_id, o_id):
    prepared = session.prepare(
        "SELECT ol_number, ol_quantity, ol_amount FROM order_line WHERE ol_w_id = ? AND ol_d_id = ? AND ol_o_id = ?")
    rows = list(session.execute(prepared.bind(
        (int(w_id), int(d_id), int(o_id)))))

    total_amount = 0

    for ol in rows:
        ol_number, ol_quantity, ol_amount = ol
        if ol_amount is not None:
            total_amount += int(ol_amount)

        prepared = session.prepare(
            "UPDATE order_line SET ol_delivery_d = ? WHERE ol_w_id = ? AND ol_d_id = ? AND ol_o_id = ?")
        session.execute(prepared.bind(
            (str(datetime.now()), int(w_id), int(d_id), int(o_id))))

    return total_amount


def update_customer(session, w_id, d_id, o_id, total_amount):
    # Get customer id
    prepared = session.prepare(
        "SELECT o_c_id FROM order_table WHERE o_w_id = ? AND o_d_id = ? AND o_id = ?")
    rows = list(session.execute(prepared.bind(
        (int(w_id), int(d_id), int(o_id)))))
    if not rows:
        return
    c_id = rows[0].o_c_id

    # Update customer
    prepared = session.prepare(
        "SELECT c_balance, c_delivery_cnt FROM customer WHERE c_w_id = ? AND c_d_id = ? AND c_id = ?")
    rows = list(session.execute(prepared.bind(
        (int(w_id), int(d_id), int(c_id)))))

    if not rows:
        return

    c_balance, c_delivery_cnt = rows[0]

    prepared = session.prepare(
        "UPDATE customer SET c_balance = ?, c_delivery_cnt = ? WHERE c_w_id = ? AND c_d_id = ? AND c_id = ?")
    session.execute(prepared.bind((c_balance + total_amount,
                                   c_delivery_cnt + 1, int(w_id), int(d_id), int(c_id))))


def delivery_xact(session, w_id, carrier_id):
    for d_id in range(1, 11):
        o_id = get_and_update_next_o_id_to_deliver(session, w_id, d_id)
        update_order(session, w_id, d_id, o_id, carrier_id)
        total_amount = update_order_lines_and_get_total_order_amount(
            session, w_id, d_id, o_id)
        update_customer(session, w_id, d_id, o_id, total_amount)
    return 'DONE! No output for this transaction!'
