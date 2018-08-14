from bottle import request, Bottle, template, static_file, abort

import json
import time
from argparse import ArgumentParser

# sys.path.append(os.getcwd() + '/domain')

from response import put_response
from log import log_info
# from getface import cutout_face, get_face_image_name, circumscribe_face
# from prob import Prob
import filemanager as fm
# html_path = "../static/html/"
from utils import camel2snake, snake2camel, convert

from gevent.pywsgi import WSGIServer
import gevent
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from models.cnn.cnn import CNN

app = Bottle()
dictionary = {}


@app.route('/')
def index_html():
    return template("index_ws")


@app.route("/test")
def index():
    return static_file('/views/index_2.html', root='./')


@app.route("/statics/<filepath:path>")
def statics(filepath):
    return static_file(filepath, root="./statics")


@app.route('/recipes', method="GET")
def get_recipes_list():
    offset = request.params.get("offset", 0)
    limit = request.params.get("limit")
    res = fm.get_recipe_list(offset, limit)
    return put_response(res)


@app.route('/recipes', method="POST")
def add_recipe():
    content_type = request.get_header('Content-Type')
    if content_type == "application/json":
        obj = request.json
        res = fm.save_recipe(obj)
    else:
        res = {"status": "error"}
    return put_response(res)


@app.route('/recipes/<recipe_id>', method="GET")
def get_recipe(recipe_id):
    res = fm.get_recipe(recipe_id)
    return put_response(res)


@app.route('/recipes/<recipe_id>', method="PUT")
def update_recipe(recipe_id):
    content_type = request.get_header('Content-Type')
    if content_type == "application/json":
        obj = request.json
        res = fm.update_recipe(recipe_id, obj)
    else:
        res = {"status": "error"}
    return put_response(res)


@app.route('/recipes/<recipe_id>', method="DELETE")
def delete_recipe(recipe_id):
    res = fm.delete_recipe(recipe_id)
    return put_response(res)


def send_message(wsock, obj):
    res = convert(obj, snake2camel)
    res_json = json.dumps(res)
    wsock.send(res_json)


def handler(wsock, message):
    if str(wsock) not in dictionary:
        dictionary[str(wsock)] = {}
        log_info("####################")
        log_info("create new wsock dict.")
        log_info("####################")
    d = dictionary[str(wsock)]
    log_info(dictionary.keys())
    try:
        obj = json.loads(message)
        print(obj)
        if obj["action"] == "startUploading":
            d["uploading_size"] = 0
            d["uploading_file"] = bytearray()

            d["action"] = obj["action"]
            d["file_size"] = obj.get("fileSize", 0)
            d["name"] = obj.get("name", "")
            d["description"] = obj.get("description", "")

            res = {
                "action": obj["action"]
            }
            send_message(wsock, res)

        elif obj["action"] == "getDataList":
            offset = obj.get("offset", 0)
            limit = obj.get("limit")
            res = fm.get_data_list()
            res["action"] = obj["action"]
            send_message(wsock, res)

        elif obj["action"] == "getData":
            offset = obj.get("offset", 0)
            limit = obj.get("limit", 10)
            data_id = obj.get("dataId")
            res = fm.get_data(data_id, offset, limit)
            res["action"] = obj["action"]
            res["dataId"] = data_id
            send_message(wsock, res)

        elif obj["action"] == "getRecipeList":
            offset = obj.get("offset", 0)
            limit = obj.get("limit")
            res = fm.get_recipe_list(offset, limit)
            res["action"] = obj["action"]
            send_message(wsock, res)

        elif obj["action"] == "getModelList":
            offset = obj.get("offset", 0)
            limit = obj.get("limit")
            res = fm.get_model_list()
            res["action"] = obj["action"]
            send_message(wsock, res)

        elif obj["action"] == "startLearning":

            recipe_id = obj["recipeId"]
            data_id = obj["dataId"]
            model_info = obj["info"]
            config = obj["trainConfig"]
            model = CNN(recipe_id)
            res = model.train(config, data_id, wsock, model_info)
            res["action"] = "finishLearning"
            del model
            send_message(wsock, res)

        elif obj["action"] == "addRecipe":
            recipe = obj["recipe"]
            res = fm.save_recipe(recipe)
            res["action"] = obj["action"]
            send_message(wsock, res)

        elif obj["action"] == "inferenceImages":
            d["uploading_size"] = 0
            d["uploading_file"] = bytearray()

            d["model_id"] = obj["modelId"]
            d["recipe_id"] = obj["recipeId"]
            d["inference_type"] = obj["type"]
            d["file_size"] = obj["fileSize"]
            file_name = obj["fileName"]
            d["file_name"] = file_name
            log_info(d)
            if "zip" == file_name.split(".")[1]:
                action = "startUploadingInferenceZip"
                d["action"] = "uploadingInferenceZip"
            else:
                action = "inferenceSingleImage"
                d["action"] = action

            res = {
                "action": action
            }
            send_message(wsock, res)

        elif obj["action"] == "deleteModel":
            model_id = obj["modelId"]
            r = fm.delete_model(model_id)
            log_info(r)
            res = {}
            res["action"] = obj["action"]
            res["modelId"] = model_id
            send_message(wsock, res)

        elif obj["action"] == "deleteRecipe":
            recipe_id = obj["recipeId"]
            r = fm.delete_recipe(recipe_id)
            log_info(r)
            res = {}
            res["action"] = obj["action"]
            res["recipeId"] = recipe_id
            send_message(wsock, res)

        elif obj["action"] == "deleteData":
            data_id = obj["dataId"]
            r = fm.delete_data(data_id)
            log_info(r)
            res = {}
            res["action"] = obj["action"]
            res["dataId"] = data_id
            send_message(wsock, res)

        elif obj["action"] == "updateData":
            data = obj["dataInfo"]
            file_id = obj["dataId"]
            new_data = fm.update_data_info(data, file_id)
            res = {
                "data": new_data,
                "action": obj["action"]
            }
            log_info(res)
            send_message(wsock, res)

        elif obj["action"] == "updateModel":
            model_id = obj["modelId"]
            model = obj["model"]
            put_res = fm.put_model_info(model, model_id)
            res = {
                "model": put_res["detail"],
                "action": obj["action"]
            }
            log_info(res)
            send_message(wsock, res)

        elif obj["action"] == "updateRecipe":
            recipe_id = obj["recipeId"]
            info = obj["info"]
            res = fm.get_recipe(recipe_id)
            if res and res.get("status") == "success":
                body = res["detail"]["body"]
                body["info"]["name"] = info["name"]
                body["info"]["description"] = info["description"]
                new_recipe = fm.update_recipe(recipe_id, body)
                res = {
                    "recipe": new_recipe["detail"],
                    "action": obj["action"]
                }
            else:
                res = {
                    "status": "error",
                    "action": obj["action"]
                }
            log_info(res)
            send_message(wsock, res)

    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        print(d["action"])
        if d["action"] == "startUploading":

            def finished(d):
                uploading_file = d["uploading_file"]
                file_id = fm.generate_id()
                result = fm.put_zip_file(uploading_file, file_id, is_expanding=True)
                info = fm.get_data_statistics(file_id)
                info["name"] = d["name"]
                info["description"] = d["description"]
                res = fm.put_data_info(info, file_id)
                res["action"] = "uploaded"
                return res

            file_uploader(d, message, wsock, "uploadingLearningData", finished)

        elif d["action"] == "uploadingInferenceZip":

            def finished(d):
                uploading_file = d["uploading_file"]
                file_id = fm.generate_id()
                result = fm.put_inference_zip(uploading_file, file_id, is_expanding=True)
                log_info(result)
                if result["status"] == "success":
                    image_path = result["image_path"]
                    model_id = d["model_id"]
                    recipe_id = d["recipe_id"]
                    model = CNN(recipe_id)
                    inference_type = d["inference_type"]
                    if inference_type == "classification":
                        inference_res = model.classify(model_id, image_path)
                        action = "finishClassfication"
                    elif inference_type == "vectorization":
                        inference_res = model.vectorize(model_id, image_path, is_similarity=True)
                        action = "finishVectorization"
                    elif inference_type == "dimRed":
                        inference_res = model.dim_reduct(model_id, image_path)
                        action = "finishDimRed"
                    res = fm.get_inferece_images(image_path)
                    image_list = res["list"]
                    res_list = []
                    for r, i in zip(inference_res, image_list):
                        r["body"] = i["body"]
                        res_list.append(r)

                    res = {
                        "action": action,
                        "id": file_id,
                        "list": res_list
                    }
                return res

            file_uploader(d, message, wsock, "uploadingInferenceZip", finished)

        elif d["action"] == "inferenceSingleImage":

            res = fm.save_inference(message)
            file_id = res["detail"]["id"]
            file_path = res["detail"]["file_path"]
            recipe_id = d["recipe_id"]
            model_id = d["model_id"]
            file_name = d["file_name"]
            model = CNN(recipe_id)
            inference_type = d["inference_type"]
            if inference_type == "classification":
                inference_res = model.classify(model_id, file_path)
                action = "finishClassfication"
            elif inference_type == "vectorization":
                inference_res = model.vectorize(model_id, file_path, is_similarity=False)
                action = "finishVectorization"
            inference_res[0]["image_name"] = file_name
            res = {
                "list": inference_res,
                "action": action
            }
            fm.delete_inference(file_id)
            del dictionary[str(wsock)]
            send_message(wsock, res)


def file_uploader(d, message, wsock, action, finished_func):
    d["uploading_size"] += len(message)
    d["uploading_file"] += message
    res = {"status": "loading", "loadedSize": d["uploading_size"], "action": action}
    time.sleep(0.05)  # for the progress bar.
    log_info(d["uploading_size"])
    log_info(action)
    send_message(wsock, res)

    if d["uploading_size"] == int(d["file_size"]):
        res = finished_func(d)
        del dictionary[str(wsock)]
        log_info("delete wsock delete")
        res["fileId"] = res.pop("id")
        send_message(wsock, res)


@app.route('/connect')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')
    global dictionary
    while True:
        try:
            message = wsock.receive()
            gevent.spawn(handler, wsock, message)
        except WebSocketError:
            print("close")
            break


@app.route('/upload', method="POST")
def upload_file():
    files = request.files
    res = fm.upload_file(files)
    if res["status"] == "success":
        name = res["detail"]["name"]
        id = res["detail"]["id"]
        save_path = fm.get_save_path(id)
        cutout_res = cutout_face(save_path, name, save_path)
        if cutout_res["status"] == "error":
            return put_response(cutout_res)
        else:
            res["detail"]["faceTotal"] = cutout_res["detail"]["number"]
        circum_res = circumscribe_face(save_path, name, save_path)
        if circum_res["status"] == "error":
            return put_response(circum_res)
    print(res)
    return put_response(res)


@app.route('/images/<image_id>/face/<number>', method="GET")
def get_face(image_id, number):
    fullpath = get_face_image_name(image_id, number)
    with open(fullpath) as f:
        image = f.read()
    content_type = fm.get_content_type(fullpath)
    return put_response(image, content_type=content_type)


@app.route('/images/<image_id>/rectangle', method="GET")
def get_rectangle(image_id):
    fullpath = get_face_image_name(image_id,type="rect")
    with open(fullpath) as f:
        image = f.read()
    content_type = fm.get_content_type(fullpath)
    return put_response(image, content_type=content_type)


@app.route('/images/<image_id>/rectangle/indiviual/<number>', method="GET")
def get_rectangle_indiviual(image_id, number):
    name = get_face_image_name(image_id, type="rect", full_path=False)
    save_path = fm.get_save_path(image_id)
    res = circumscribe_face(save_path, name[5:], save_path, int(number))
    fullpath = save_path + "/" + name
    with open(fullpath) as f:
        image = f.read()
    content_type = fm.get_content_type(fullpath)
    return put_response(image, content_type=content_type)


@app.route('/images/<image_id>/probability', method="GET")
def get_probability(image_id):
    res = prob.get_prob(image_id)
    return put_response(res)


@app.route('/static/<file_type>/<file>')
def read_static(file_type, file):
    if file_type == "js":
        content_type = "text/javascript"
    elif file_type == "css":
        content_type = "text/css"
    else:
        content_type = "text/html"
    with open('../static/'+file_type+'/'+file) as f:
        data = f.read()
    return put_response(data=data, content_type=content_type)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--port', dest="port", type=int, default=8081)
    parser.add_argument('--debug', dest="debug", action="store_true")
    args = parser.parse_args()
    port = args.port
    if args.debug:
        log_info("debug mode.")
        app.run(host="0.0.0.0", port=8081, debug=True, reloader=True)
    else:
        server = WSGIServer(("0.0.0.0", port), app, handler_class=WebSocketHandler)
        log_info("websocket server start. port:{}".format(port))
        server.serve_forever()
