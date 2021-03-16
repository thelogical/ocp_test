from flask import Flask, request, make_response
import requests
import torchvision
import shutil
from PIL import Image 
import os
from webptools import dwebp
from webptools import grant_permission
import torchvision.transforms as T
from flask import jsonify
import mysql.connector


#grant_permission()


app = Flask(__name__)

def get_prediction(img_path, threshold=0.7):

	model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
	model.eval()

	COCO_INSTANCE_CATEGORY_NAMES = [
	'__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
	'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
	'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
	'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
	'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
	'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
	'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
	'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
	'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'dining table',
	'N/A', 'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
	'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
	'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

	img = Image.open(os.getcwd()+'/'+img_path) # Load the image
	transform = T.Compose([T.ToTensor()]) # Defing PyTorch Transform
	img = transform(img) # Apply the transform to the image
	pred = model([img]) # Pass the image to the model
	pred_class = [COCO_INSTANCE_CATEGORY_NAMES[i] for i in list(pred[0]['labels'].numpy())] # Get the Prediction Score
	pred_boxes = [[(i[0], i[1]), (i[2], i[3])] for i in list(pred[0]['boxes'].detach().numpy())] # Bounding boxes
	pred_score = list(pred[0]['scores'].detach().numpy())
	pred_t = [pred_score.index(x) for x in pred_score if x > threshold][-1] # Get list of index with score greater than threshold.
	pred_boxes = pred_boxes[:pred_t+1]
	pred_class = pred_class[:pred_t+1]
	return pred_boxes, pred_class

def get_objects(imurl,request):

	r = requests.get(imurl,stream=True)
	if r.status_code == 200:
		r.raw.decode_content = True

		with open("tmp.webp",'wb') as f:
			shutil.copyfileobj(r.raw, f)

		dwebp(input_image="tmp.webp", output_image="tmp.png",
            option="-o")

		boxes, classes = get_prediction("tmp.png")
		classes = list(set(classes))
		con = mysql.connector.connect(autocommit=True,host=os.getenv('MYSQL_SERVER'),user=os.getenv('MYSQL_USER'),passwd=os.getenv('MYSQL_PASS'),auth_plugin="mysql_native_password",database=os.getenv('MYSQL_DATABASE'));
		cur = con.cursor()
		query = "update user_data set last_access=current_timestamp() where uname='{}'".format(request.form['user']) 
		cur.execute(query)
		query = "update user_data set objects=objects + {} where uname='{}'".format(len(classes),request.form['user'])
		cur.execute(query)
		con.close()
		return jsonify(objects=classes)

     
def authorize(request):
	con = mysql.connector.connect(autocommit=True,host=os.getenv('MYSQL_SERVER'),user=os.getenv('MYSQL_USER'),passwd=os.getenv('MYSQL_PASS'),auth_plugin="mysql_native_password",database=os.getenv('MYSQL_DATABASE'));
	cur = con.cursor();
	query = "select pass from user_data where uname='root'"
	cur.execute(query);
	res = cur.fetchall();
	actual = res[0][0]
	con.close()
	if actual==request.form['pass']:
		return True
	else:
		return False



@app.route('/')
def hello():
    return "Hello World!"

@app.route('/imurl', methods=['POST'])
def im_url():
        if os.getenv('MYSQL_PORT'):
                socket = os.getenv['MYSQL_PORT']
                host = socket.split('//')[-1].split(':')[0]
                os.environ['MYSQL_SERVER'] = host
	auth = authorize(request)
	if not auth:
		d = {"Error": "Incorrect username or password"}
		return make_response(jsonify(d), 403)
	imurl=request.form['url']
	return get_objects(imurl,request)

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8080)
