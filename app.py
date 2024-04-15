from flask import Flask, request, jsonify
from flask_cors import CORS
from globals import qrs, qrs_lock
from sites import sites, sites_lock
from operator import itemgetter
import uuid
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
CORS(app)  # Active CORS pour toutes les routes

def distanceEnKm(lat1, lon1, lat2, lon2):
    # Rayon moyen de la Terre en kilomètres
    R = 6371.0
    # Conversion des chaînes de caractères en nombres (float)
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    # Conversion des degrés en radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    # Différence des latitudes et longitudes
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Formule de la distance haversine
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Distance en kilomètres
    distance = R * c

    return distance

# Endpoint pour recherche du site le plus proche
@app.route('/getSite', methods=['GET'])
def get_site():
    latIn = request.args.get('latitude')
    if latIn is None:
        return jsonify({'error': 'Le paramètre "latitude" est requis'}), 400
    longIn = request.args.get('longitude')
    if longIn is None:
        return jsonify({'error': 'Le paramètre "longitude" est requis'}), 400

    distanceLaPlusPetite=9999
    leSiteLePlusProche = 'SPL'
    with sites_lock:
        for site in sites:
            if distanceEnKm(latIn, longIn, site['latitude'],  site['longitude']) < distanceLaPlusPetite :
                leSiteLePlusProche = site['site']
                distanceLaPlusPetite = distanceEnKm(latIn, longIn, site['latitude'],  site['longitude'])

    print('distanceLaPlusPetite =' + str(distanceLaPlusPetite))
    return jsonify({'site': leSiteLePlusProche, 'distance': distanceLaPlusPetite})


# Endpoint pour le service "getList"
@app.route('/getList', methods=['GET'])
def get_list():
    site_param = request.args.get('site')

    if site_param is None:
        return jsonify({'error': 'Le paramètre "site" est requis'}), 400

    with qrs_lock:
        filtered_qrs = [qr for qr in qrs if qr['site'] == site_param and (qr['status'] == 'NEW' or qr['status'] == 'SCANNED')]

    sorted_qrs = sorted(filtered_qrs, key=lambda x: (x['status'], x['rest_home_name']), reverse=True)
 

    response_data = sorted_qrs
    return jsonify(response_data)

# Endpoint pour le service "setStatus"
@app.route('/setStatus', methods=['GET', 'POST'])
def set_status():
    if request.method == 'GET':
        qrcode_param = request.args.get('qrcode')
        status_param = request.args.get('status')
    elif request.method == 'POST':
        qrcode_param = request.json.get('qrcode')
        status_param = request.json.get('status')
    else:
        return jsonify({'error': 'Méthode non autorisée'}), 405

    if qrcode_param is None:
        return jsonify({'error': 'Le paramètre "qrcode" est requis'}), 400

    site = 'NotFound'
    with qrs_lock:
        for qr in qrs:
            if qr['qrcode'] == qrcode_param:
                qr['status'] = status_param
                site = qr['site']
                break

    return jsonify({'site': site})

# Endpoint pour le service "setStatutScanned"
@app.route('/setStatutScanned', methods=['GET', 'POST'])
def set_statut_scanned():
    if request.method == 'GET':
        qrcode_param = request.args.get('qrcode')
        qui_param = request.args.get('qui')
    elif request.method == 'POST':
        qrcode_param = request.json.get('qrcode')
        qui_param = request.json.get('qui')
    else:
        return jsonify({'error': 'Méthode non autorisée'}), 405

    if qrcode_param is None:
        return jsonify({'error': 'Le paramètre "qrcode" est requis'}), 400

    with qrs_lock:
        for qr in qrs:
            if qr['qrcode'] == qrcode_param:
                qr['status'] = 'SCANNED'
                site = qr['site']
                if qui_param is not None:
                    qr['qui'] = qui_param
                break

    return jsonify({'site': site})

# Endpoint pour le service "setStatutScanned"
@app.route('/bacPlein', methods=['GET', 'POST'])
def bacPlein():
    if request.method == 'GET':
        qrcode_param = request.args.get('qrcode')
        qui_param = request.args.get('qui')
    elif request.method == 'POST':
        qrcode_param = request.json.get('qrcode')
        qui_param = request.json.get('qui')
    else:
        return jsonify({'error': 'Méthode non autorisée'}), 405

    if qrcode_param is None:
        return jsonify({'error': 'Le paramètre "qrcode" est requis'}), 400

    new_qrcode = str(uuid.uuid4())

    with qrs_lock:
        for qr in qrs:
            if qr['qrcode'] == qrcode_param:
                new_record = qr.copy()
                new_record['qrcode'] = new_qrcode
                new_record['status'] = 'NEW'
                qrs.append(new_record)
                new_record['bacAdded'] = 1

                break

    return jsonify({'result':'OK'})

# Endpoint pour le service "sendChronos"
@app.route('/sendChronos', methods=['GET'])
def sendChronos():

    with qrs_lock:
        for qr in qrs:
            if qr['status'] == 'SCANNED':
                qr['status'] = 'SENT'


    return jsonify({'result':'OK'})




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
