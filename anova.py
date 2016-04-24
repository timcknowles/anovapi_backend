"""
Example of using pycirculate with a simple Flask RESTful API.
Make sure to send requests with the HTTP header "Content-Type: application/json".
"""
from flask import Flask, request, jsonify, abort, make_response, render_template
from flask.ext.cors import CORS
from pycirculate.anova import AnovaController
import logging
import sys
logging.getLogger('flask_cors').level = logging.DEBUG
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

ANOVA_MAC_ADDRESS = "F4:B8:5E:AF:F8:D6"


# Error handlers

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request.'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found.'}), 404)

@app.errorhandler(500)
def server_error(error):
    return make_response(jsonify({'error': 'Server error.'}), 500)

def make_error(status_code, message, sub_code=None, action=None, **kwargs):
    """
    Error with custom message.
    """
    data = {
        'status': status_code,
        'message': message,
    }
    if action:
        data['action'] = action
    if sub_code:
        data['sub_code'] = sub_code
    data.update(kwargs)
    response = jsonify(data)
    response.status_code = status_code
    return response

# REST endpoints

@app.route('/', methods=["GET","POST"])
def index():
    try:
        with AnovaController(ANOVA_MAC_ADDRESS) as ctrl:
            output = {"anova_status": ctrl.anova_status()}
    except Exception as exc:
        app.logger.error(exc)
        return make_error(500, "{0}: {1}".format(repr(exc), str(exc)))

    return jsonify(output)

@app.route('/temp', methods=["GET"])
def get_temp():
    try:
        with AnovaController(ANOVA_MAC_ADDRESS) as ctrl:
            output = {"current_temp": ctrl.read_temp(), "set_temp": ctrl.read_set_temp(), "unit": ctrl.read_unit(),}
    except Exception as exc:
        app.logger.error(exc)
        return make_error(500, "{0}: {1}".format(repr(exc), str(exc)))

    return jsonify(output)

@app.route('/temp', methods=["POST"])
def set_temp():
    try:
        temp = request.get_json()['temp']
    except (KeyError, TypeError):
        abort(400)
    temp = float(temp)
    with AnovaController(ANOVA_MAC_ADDRESS) as ctrl:
        output = {"set_temp": ctrl.set_temp(temp)}

    return jsonify(output)

@app.route('/stop', methods=["POST"])
def stop_anova():
  
    with AnovaController(ANOVA_MAC_ADDRESS) as ctrl:
        output = {"status": ctrl.stop_anova()}

    return jsonify(output)

@app.route('/start', methods=["POST"])
def start_anova():
    with AnovaController(ANOVA_MAC_ADDRESS) as ctrl:
        output = {"status": ctrl.start_anova()}

    return jsonify(output)

@app.route('/api', methods = ['GET'])
def this_func():
    """This is a function. It does nothing."""
    return jsonify({ 'result': '' })

@app.route('/api/help', methods = ['GET'])
def help():
    """Print available functions."""
    func_list = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = app.view_functions[rule.endpoint].__doc__
    return jsonify(func_list)

@app.route('/control')
def control():
	return render_template('control.html')

if __name__ == '__main__':
    # Setup logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    app.run(host='0.0.0.0')
