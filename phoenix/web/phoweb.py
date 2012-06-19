from flask import Flask
from flask import render_template
from werkzeug.exceptions import abort
from phoenix import fabfile
from phoenix.plogging import logger

app = Flask(__name__)

config_location="../../samples"
property_file="../../build_credentials/phoenix.ini"

@app.route("/")
def hello():
    definitions = fabfile.get_list_of_environment_definitions(config_dir=config_location, property_file=property_file)
    return render_template('index.html', definitions=definitions)

@app.route("/details/<defname>")
def definition_details(defname):
    definitions = fabfile.get_list_of_environment_definitions(config_dir=config_location, property_file=property_file)

    for definition in definitions:
        if definition.name == defname:
            return render_template("def_details.html", definition=definition)

    return page_not_found("No such template %s" % defname)

@app.errorhandler(404)
def page_not_found(user_visible_error):
    return render_template('404.html', user_visible_error=user_visible_error), 404

if __name__ == "__main__":
    app.run(debug=True)