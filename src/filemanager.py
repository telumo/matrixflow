import os
import shutil
import base64
import datetime
import json
from pathlib import Path
import tensorflow as tf
import pandas as pd
import zipfile_utf8

recipe_dir = "./recipes"
data_dir = "./data"
model_dir = "./logs"
inference_dir = "./inference"

os.makedirs(model_dir, exist_ok=True)


allow_file = ["jpeg", "png", "jpg", "JPEG", "JPG", "PNG"]



def generate_id():
    """
     generate ids which are same as file paths.
    """
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def get_create_time(p):
    """
    p Path object
    """
    epoch_time = os.path.getctime(p)
    create_time = datetime.datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")
    return create_time


def get_update_time(p):
    """
    p Path object
    """
    epoch_time = os.path.getmtime(p)
    update_time = datetime.datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")
    return update_time


def save_json(obj, file_path):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def get_images(images_path):
    images = []
    for ext in allow_file:
        images += list(images_path.glob("*."+ext))
    return images


################ data start########################

def get_data_path(file_id):
    return Path(data_dir) / file_id


def get_data_statistics(file_id):
    label_dir = Path(data_dir) / file_id / "labels"
    label_path_list = list(label_dir.glob("*.csv"))
    if len(label_path_list) == 0:
        return {}
    label_path = label_path_list[0]
    df = pd.read_csv(label_path, names=["filename", "label"])
    df_count = df.groupby("label").count()
    n_classes = len(df_count)
    d = {}
    for r in df_count.itertuples():
        d[str(r[0])] = r[1]
    res = {
        "nClasses": n_classes,
        "statistics": d
    }
    return res


def put_zip_file(file, file_id, is_expanding=False):
    """
      file: bitearray
      file_id: string
    """
    p = Path(data_dir) / file_id
    os.makedirs(p / "tmp", exist_ok=True)
    tmp = p / "tmp"
    file_path = tmp / "data.zip"
    with open(file_path, "wb") as f:
        f.write(file)

    if is_expanding:
        with zipfile_utf8.ZipFile(file_path) as zf:
            try:
                zf.extractall(tmp)

                for type in ["images", "texts", "labels"]:
                    g = "*/"+type
                    image_dir =tmp.glob(g)
                    l =  list(image_dir)
                    if len(l) > 0:
                        d = l[0]
                        print("#$###")
                        print(d)
                        print("#$###")
                        os.rename(d, p / type)
                shutil.rmtree(tmp)

            except Exception as e:
                shutil.rmtree(tmp)
                print(e)
                return {"status": "error"}
    return {"status": "success"}


def put_data_info(new_data, file_id):
    p = Path(data_dir) / file_id
    info_path = p / "info"
    os.makedirs(info_path, exist_ok=True)
    file_path = info_path / "info.json"
    save_json(new_data, file_path)
    return get_data_info(p)


def update_data_info(new_info, file_id):
    path = Path(data_dir) / file_id
    info = get_data_info(path)
    for k,v in new_info.items():
        info[k] = v
    res = put_data_info(info, file_id)
    return res

def get_data(data_id, offset, limit):
    p = Path(data_dir) / data_id
    if not p.exists():
        res = {
            "status": "error",
        }
        return res

    images_path = p / "images"
    labels_path = p / "labels" / "labels.csv"
    images = get_images(images_path)

    if len(images):
        texts_path = p / "texts"
        ext = "txt"
        texts = list(texts_path.glob("*."+ext))

    if (limit - offset) > len(images) or offset > len(images):
        res = {
            "status": "error",
        }
        return res

    data = images[offset: limit]
    dic_list = []
    for d in data:
        name = d.name
        with open(labels_path) as f:
            for line in f:
                l = line.split(",")
                if(l[0] == name):
                    label = l[1]
                    break
        images_dic = {
            "name": name,
            "body": base64.encodestring(open(d, 'rb').read()).decode("utf-8"),
            "label": label
        }
        dic_list.append(images_dic)
    length = len(images)
    res = {
        "status": "success",
        "data_type": "list",
        "total": length,
        "list": dic_list
    }
    return res


def get_data_info(path):
    """
     path pathlib.Path
    """
    if not path.exists():
        return {}

    images = path / "images"
    texts_path = path / "texts"
    labels = path / "labels" / "labels.csv"
    info = path / "info" / "info.json"
    id = path.name
    n_images = 0
    for ext in allow_file:
        n_images += len(list(images.glob("*."+ext)))

    ext = "txt"
    n_texts = len(list(texts_path.glob("*."+ext)))

    if info.exists():
        with open(info, "r") as f:
            body = json.load(f)
        update_time = get_update_time(info)
    else:
        body = {}
        update_time = get_update_time(path)

    if labels.exists():
        with open(labels, "r") as f:
            n_labels = len(f.readlines())
    else:
        n_labels = 0

    create_time = get_create_time(path)
    data = {
        "id": id,
        "nTexts": n_texts,
        "nImages": n_images,
        "nLabels": n_labels,
        "nClasses": body.get("nClasses", 0),
        "statistics": body.get("statistics", {}),
        "name": body.get("name", ""),
        "description": body.get("description", ""),
        "update_time": update_time,
        "create_time": create_time
    }
    return data

def get_data_list():
    p = Path(data_dir)
    p_list = [x for x in p.iterdir() if x.is_dir()]
    length = len(p_list)
    data = []
    for path in p_list:
        d = get_data_info(path)
        data.append(d)
    res = {
            "status": "success",
            "data_type": "list",
            "total": length,
            "list": data
    }
    return res

def delete_data(id):
    p = Path(data_dir) / id
    if os.path.isdir(p):
        shutil.rmtree(p)
    res = {
        "status": "success",
        "data_type": "delete"
    }
    return res


################ data endt########################


################ model start########################

def get_model_info(model_id):
    p = Path(model_dir) / model_id / "info" / "info.json"
    with open(p, "r") as f:
        body = json.load(f)
    body["id"] = model_id
    body["create_time"] = get_create_time(p)
    body["update_time"] = get_update_time(p)
    res = {
        "status": "success",
        "data_type": "detail",
        "detail": body
    }
    return res


def put_model_info(new_model, model_id):
    info_dir = Path(model_dir) / model_id / "info"
    os.makedirs(info_dir, exist_ok=True)
    info_path = info_dir / "info.json"
    save_json(new_model, info_path)
    return get_model_info(model_id)


def get_model_list():
    p = Path(model_dir)
    p_list = [x for x in p.iterdir() if x.is_dir()]
    length = len(p_list)
    models = []
    for j in p_list:
        id = j.name
        info = j / "info" / "info.json"
        if info.exists():
            with open(info, "r") as f:
                body = json.load(f)
            update_time = get_update_time(info)
        else:
            body = {}
            update_time = get_update_time(j)

        sum_path = j / "summaries"
        chartData = {}
        for t in sum_path.glob("*/*"):
            name = t.parent.name # test or train
            chartData[name] = {
                "accuracy": [],
                "loss": [],
                "step": []
            }
            t_str = str(t)
            for e in tf.train.summary_iterator(t_str):
                if int(e.step):
                    chartData[name]["step"].append(e.step)
                for v in e.summary.value:
                    if v.tag == 'accuracy_1':
                        chartData[name]["accuracy"].append(v.simple_value)
                    elif v.tag == 'loss_1':
                        chartData[name]["loss"].append(v.simple_value)

        create_time = get_create_time(j)
        body["id"] = id
        body["chartData"] = chartData
        body["update_time"] = update_time
        body["create_time"] = create_time
        models.append(body)
    res = {
            "status": "success",
            "data_type": "list",
            "total": length,
            "list": models
    }
    return res

def delete_model(id):
    p = Path(model_dir) / id
    if os.path.isdir(p):
        shutil.rmtree(p)
    res = {
        "status": "success",
        "data_type": "delete"
    }
    return res


################ model end ########################


################ inference start ########################

def get_inference_path(file_id):
    return Path(inference_dir) / file_id

def save_inference(file):
    dir_name = generate_id()
    dir_path = get_inference_path(dir_name)
    dir_path.mkdir()
    file_path = os.path.join(dir_path, "tmp.jpg")
    with open(file_path, "wb") as f:
        f.write(file)

    res = {
        "status": "success",
        "data_type": "detail",
        "detail": {"id": dir_name, "file_path": file_path}
    }
    return res


def delete_inference(id):
    p = Path(inference_dir) / id
    if os.path.isdir(p):
        shutil.rmtree(p)
    res = {
        "status": "success",
        "data_type": "delete"
    }
    return res

def get_inferece_images(image_path):
    images = get_images(image_path)
    target_images = images # for offset and limit
    length = len(images)
    dic_list = [{
        "name": path.name,
        "body": base64.encodestring(open(path, 'rb').read()).decode("utf-8"),
        } for path in target_images]
    res = {
        "status": "success",
        "data_type": "list",
        "total": length,
        "list": dic_list
    }
    return res


def put_inference_zip(file, file_id, is_expanding=False):
    """
      file: bitearray
      file_id: string
    """
    p = get_inference_path(file_id)
    tmp = p / "tmp"
    tmp.mkdir(parents=True)
    file_path = tmp / "data.zip"
    with open(file_path, "wb") as f:
        f.write(file)

    if is_expanding:
        with zipfile_utf8.ZipFile(file_path) as zf:
            try:
                zf.extractall(tmp)
                image_dir =tmp.glob("*/images")
                d =  next(image_dir)
                os.rename(d, p / "images")
                shutil.rmtree(tmp)

            except Exception as e:
                shutil.rmtree(tmp)
                print(e)
                return {"status": "error"}
    return {
        "status": "success",
        "file_path": p,
        "image_path": p / "images"
    }

################ inference end ########################


################ recipe start ########################



def save_recipe(obj):
    dir_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    dir_path = Path(recipe_dir) / dir_name
    dir_path.mkdir()
    file_path = os.path.join(dir_path, "recipe.json")
    save_json(obj, file_path)
    res = {
        "status": "success",
        "data_type": "detail",
        "detail": {"id": dir_name, "body": obj}
    }
    return res

def get_recipe_list(offset=0, limit=None):
    offset = int(offset)
    recipes = []
    p = Path(recipe_dir)
    p_list = list(p.glob("*/*.json"))
    length = len(p_list)
    if limit is not None:
        limit = int(limit)
        p_list = p_list[offset:limit]
    else:
        p_list = p_list[offset:]
    for j in p_list:
        id = j.parent.name
        with open(j, "r") as f:
            body = json.load(f)

        create_time = get_create_time(j)
        update_time = get_update_time(j)
        rec = {
            "id": id,
            "body": body,
            "update_time": update_time,
            "create_time": create_time
        }
        recipes.append(rec)
    res = {
            "status": "success",
            "data_type": "list",
            "total": length,
            "list": recipes
        }
    return res

def get_recipe(id):
    p = Path(recipe_dir) / id / "recipe.json"
    with open(p, "r") as f:
        body = json.load(f)
    create_time = get_create_time(p)
    update_time = get_update_time(p)
    recipe = {
        "id": id,
        "body": body,
        "update_time": update_time,
        "create_time": create_time
    }
    res = {
        "status": "success",
        "data_type": "detail",
        "detail": recipe
    }
    return res

def update_recipe(id, obj):
    p = Path(recipe_dir) / id / "recipe.json"
    save_json(obj, p)
    return get_recipe(id)

def delete_recipe(id):
    p = Path(recipe_dir) / id
    if os.path.isdir(p):
        shutil.rmtree(p)
    res = {
        "status": "success",
        "data_type": "delete"
    }
    return res

################ recipe end ########################
