# qc/box_catalog.py

BOX_SPECS = [
    {"code":"001","size":[32.0,18.0,25.0],"weight_g":300,"volume_cm3":14400.0,"type":"BOX"},
    {"code":"002","size":[21.0,18.0,21.0],"weight_g":220,"volume_cm3":7938.0,"type":"BOX"},
    {"code":"003","size":[28.0,21.0,9.0],"weight_g":220,"volume_cm3":5292.0,"type":"BOX"},
    {"code":"005","size":[35.0,75.0,0.1],"weight_g":100,"volume_cm3":262.5,"type":"BOX"},
    {"code":"007","size":[41.0,36.0,38.0],"weight_g":490,"volume_cm3":56088.0,"type":"BOX"},
    {"code":"008","size":[33.0,29.0,33.0],"weight_g":660,"volume_cm3":31581.0,"type":"BOX"},
    {"code":"009","size":[16.5,9.0,8.0],"weight_g":60,"volume_cm3":1188.0,"type":"BOX"},
    {"code":"010","size":[16.0,17.5,6.5],"weight_g":120,"volume_cm3":1820.0,"type":"BOX"},
    {"code":"012","size":[28.5,19.5,5.5],"weight_g":180,"volume_cm3":3056.62,"type":"BOX"},
    {"code":"015","size":[16.0,8.0,4.0],"weight_g":40,"volume_cm3":512.0,"type":"BOX"},
    {"code":"025","size":[8.0,8.0,23.0],"weight_g":40,"volume_cm3":1472.0,"type":"BOX"},
    {"code":"026","size":[12.0,12.0,36.0],"weight_g":190,"volume_cm3":5184.0,"type":"BOX"},
    {"code":"027","size":[21.0,27.0,8.0],"weight_g":140,"volume_cm3":4536.0,"type":"BOX"},
    {"code":"042","size":[32.0,18.0,21.0],"weight_g":130,"volume_cm3":12096.0,"type":"BOX"},
    {"code":"043","size":[21.0,18.0,21.0],"weight_g":100,"volume_cm3":7938.0,"type":"BOX"},
    {"code":"044","size":[42.0,32.0,18.0],"weight_g":670,"volume_cm3":24192.0,"type":"BOX"},
    {"code":"045","size":[13.0,13.0,39.0],"weight_g":100,"volume_cm3":6591.0,"type":"BOX"},
    {"code":"046","size":[49.0,14.0,26.0],"weight_g":220,"volume_cm3":17836.0,"type":"BOX"},
    {"code":"050","size":[33.0,29.0,28.0],"weight_g":320,"volume_cm3":26796.0,"type":"BOX"},
    {"code":"037","size":[23.0,12.5,0.1],"weight_g":10,"volume_cm3":28.75,"type":"ENVELOPE"},
    {"code":"101","size":[33.0,49.0,0.1],"weight_g":20,"volume_cm3":12049.4,"type":"PLASTIC"},
    {"code":"102","size":[31.0,17.0,0.1],"weight_g":10,"volume_cm3":13175.0,"type":"PLASTIC"},
    {"code":"103","size":[60.0,80.0,0.1],"weight_g":40,"volume_cm3":24000.0,"type":"PLASTIC"},
    {"code":"104","size":[50.0,40.0,0.1],"weight_g":30,"volume_cm3":20000.0,"type":"PLASTIC"},
]

BOX_CATALOG = {b["code"]: b for b in BOX_SPECS}


def get_box_spec(code: str):
    """
    Ambil spesifikasi box dari code (string).
    Return None kalau tidak ada.
    """
    if code is None:
        return None
    return BOX_CATALOG.get(str(code).zfill(3))  # jaga2 “7” → “007”
