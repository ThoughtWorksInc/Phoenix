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
    definition = get_named_definition(defname)

    if definition:
        return render_template("def_details.html", definition=definition)

    return page_not_found("No such template %s" % defname)


def get_named_definition(defname):
    definitions = fabfile.get_list_of_environment_definitions(config_dir=config_location, property_file=property_file)
    for definition in definitions:
        if definition.name == defname:
            return definition
    return None

@app.route("/service/<servicename>")
def service_details(servicename):
    service_definitions = fabfile.service_defs_from_dir(config_location)

    if service_definitions.has_key(servicename):
        return render_template("service.html", service_definition=service_definitions[servicename])

    return page_not_found("No such service %s" % servicename)

@app.route("/providers")
def node_providers():
    definitions = fabfile.environment_definitions(directory=config_location, property_file=property_file)

    providers = {}
    for definition in definitions.values():
        node_provider = definition.node_provider
        if not providers.has_key(node_provider):
            providers[node_provider] = []

        providers[node_provider].append(definition.env_def_name)

    return render_template("providers.html", providers = providers)

@app.route("/running_nodes_in/<environment_template_name>")
def running_nodes_in_template(environment_template_name):
    definitions = fabfile.environment_definitions(directory=config_location, property_file=property_file)

    if definitions.has_key(environment_template_name):
        definition = definitions[environment_template_name]
        provider = definition.node_provider
        nodes = provider.list(None)

        if len(nodes) > 0:
            attributes = nodes[0].attributes().keys()
        else:
            attributes = []

        return render_template("nodes_in_template.html", nodes = nodes, attributes = attributes)

    return page_not_found("No such template %s" % environment_template_name)

@app.route("/services")
def services():
    service_definitions = fabfile.service_defs_from_dir(config_location).values()

    return render_template("services.html", service_definitions=service_definitions)


@app.errorhandler(404)
def page_not_found(user_visible_error):
    return render_template('404.html', user_visible_error=user_visible_error), 404

if __name__ == "__main__":
    app.run(debug=True)