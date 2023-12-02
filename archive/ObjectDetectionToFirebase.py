import os 
import glob
from transformers import AutoImageProcessor, AutoModelForObjectDetection
import torch
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

# Local
from Analytics import Analytics


def get_jpg_files():
    cwd = os.getcwd()
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    path = '\\'.join(cwd.split("\\")[:-1])
    img_path = "goRTCServer"
    img_full_path = os.path.join(path,img_path)
    jpg_files = glob.glob(os.path.join(img_full_path,"*.jpg"))
    
    return jpg_files

def delete_jpg_file(file):
    if file.endswith('.jpg'):
        os.remove(file)


# manual implementation of obj_detector = pipeline("object-detection", model=model_name) 
#                          obj_detector(image)
def init_manual_huggingface(model_name="facebook/detr-resnet-50"):
    image_processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModelForObjectDetection.from_pretrained(model_name)

    return image_processor, model

def predict(model, image_processor, image, print_results=False):
    with torch.no_grad():
        inputs = image_processor(images=image, return_tensors="pt")
        outputs = model(**inputs)
        target_sizes = torch.tensor([image.size[::-1]])
        results = image_processor.post_process_object_detection(outputs, threshold=0.5, target_sizes=target_sizes)[0]

    if print_results:
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [round(i, 2) for i in box.tolist()]
            print(
                f"Detected {model.config.id2label[label.item()]} with confidence "
                f"{round(score.item(), 3)} at location {box}"
            )

    return results 
# #
#

def plot_image_results(image, results, model, plot=False):
    
    draw = ImageDraw.Draw(image)

    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        box = [round(i, 2) for i in box.tolist()]
        x, y, x2, y2 = tuple(box)
        draw.rectangle((x, y, x2, y2), outline="red", width=1)
        draw.text((x, y), model.config.id2label[label.item()], fill="white")

    if plot:
        plt.figure()
        plt.imshow(image)
        plt.show()


def main(image_processor, model, uid, debug=False, print_results=False):

    # How frequent to upload analytics to firebase unit: prediction iterations
    # A frame per second is gather so roughly predictions ~= seconds
    uploadInterval = 30 # 180  

    ay = Analytics(model, uid, uploadInterval)
    files = get_jpg_files()

    # for file in files:
    while len(files) > 0:

        # get first file
        file = files[0]

        # Open File
        img = Image.open(file,mode='r')

        # Inference
        results = predict(model, image_processor, img, print_results)

        # process and save results  
        passed_results = ay.analytics(results)

        if print_results:
            # plot image
            plot_image_results(img, passed_results, model)

        # delete file
        if debug:
            if len(passed_results['scores']) == 0:
                delete_jpg_file(file)
        else:
            delete_jpg_file(file)

        files = get_jpg_files()


if __name__ == "__main__":

    uid = "RJ0pPZEpmqPdiwMNBsuErIKU8zI3" # hardcode uid
    debug = False   # if false delete every image after prediction/upload

    image_processor, model = init_manual_huggingface()
    main(image_processor, model, uid, debug)

    print("ML Done")
