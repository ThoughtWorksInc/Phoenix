from flask import Flask
from flask import render_template
from phoenix import fabfile
from phoenix.plogging import logger

app = Flask(__name__)

config_location="../../samples"
property_file="../../build_credentials/phoenix.ini"

@app.route("/")
def hello():
    definitions = fabfile.get_list_of_environment_definitions(config_dir=config_location, property_file=property_file)
    return render_template('index.html', definitions=definitions)

if __name__ == "__main__":
    app.run(debug=True)