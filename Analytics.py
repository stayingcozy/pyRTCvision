import torch
from RollingAverage import RollingAverage
from Firebase import Firebase

class Analytics():
    def __init__(self, model, uid, uploadInterval=180):
        self.model = model
        self.predictionsMade = 0
        self.uploadInterval = uploadInterval
        self.uid = uid

        self.dogroll = RollingAverage(uploadInterval) 
        self.catroll = RollingAverage(uploadInterval) 
        self.personroll = RollingAverage(uploadInterval) 

        self.fb = Firebase(uid)

        self.acceptable_classes = ["dog", "cat", "person"]
        self.past_pred = {key: None for key in self.acceptable_classes}


    def _scoreFilter(self, results):

        # threshold in post_process_object_detection does this

        passedPredictions = []

        for i in range(len(results)):
            if (results[i]["score"] > 0.5):
                passedPredictions.append(results[i])
            
        return passedPredictions

    def _classFilter(self, label):

        if label in self.acceptable_classes:
            return True
        
    def _centerpoint(self, box):
        # Data format:
        # bbox: [x, y, width, height]
        #
        #     (x, y)       (x + width, y)
        #     +----------------------+
        #     |                      |
        #     |                      |
        #     |                      |
        #     +----------------------+
        # (x, y + height)     (x + width, y + height)
        #
        # x, y, x2, y2 = tuple(box)
        # draw.rectangle((x, y, x2, y2), outline="red", width=1)

        x, y, x2, y2 = tuple(box)
        xc = x + ((x2-x)/2)
        yc = y + ((y2-y)/2)

        return [xc, yc]

    def _velocity(self, curr_pred, spelledOutLabel):
        # past_pred contains the past class and past bb center
        
        distanceDifference = 0

        currCenter = curr_pred[spelledOutLabel]

        if spelledOutLabel in self.past_pred:
            pastCenter = self.past_pred[spelledOutLabel]

            distanceDifference = abs(currCenter[0] - pastCenter[0]) + abs(currCenter[1] - pastCenter[1])

        return distanceDifference

    def uploadFirebase(self):
        # Upload average activity to firebase
        self.fb.addData(self.dogroll.getAverage(), self.catroll.getAverage(), self.personroll.getAverage())

    def analytics(self, results):

        # break results to filter by class
        scores = results["scores"]
        labels = results["labels"]
        boxes = results["boxes"]

        # Count set so if none detected activity of zero will be placed
        dogCount = 0
        catCount = 0
        personCount = 0

        passedArray = torch.zeros(scores.size(), dtype=torch.bool)
        passedBB = torch.zeros(boxes.size(), dtype=torch.bool)

        iter = 0
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [round(i, 2) for i in box.tolist()]

            spelledOutLabel = self.model.config.id2label[label.item()]
            if self._classFilter(spelledOutLabel):
                passedArray[iter] = True
                passedBB[iter,:] = True

                bb_center = self._centerpoint(box)
                pred_center = {spelledOutLabel: bb_center}

                if self.past_pred[spelledOutLabel] is not None:
                    distance_diff = self._velocity(pred_center, spelledOutLabel)

                    if (distance_diff > 0):

                        # Based off class update rolling average
                        match spelledOutLabel:
                            case "dog":
                                self.dogroll.addValue(distance_diff)
                                dogCount += 1
                            case "cat":
                                self.catroll.addValue(distance_diff)
                                catCount += 1
                            case "person":
                                self.personroll.addValue(distance_diff)
                                personCount += 1
                            case _:
                                print("No accepted class found")

                # Record current prediction bb to past for next iter
                self.past_pred[spelledOutLabel] = pred_center[spelledOutLabel]

            iter += 1


        # If no detection was made, make note of no motion for rolling average
        if dogCount<1:
            self.dogroll.addValue(0)
        if catCount<1:
            self.catroll.addValue(0)
        if personCount<1:
            self.personroll.addValue(0)

        self.predictionsMade += 1

        results["scores"] = torch.masked_select(scores,passedArray)
        results["labels"] = torch.masked_select(labels,passedArray)
        results["boxes"] = torch.masked_select(boxes,passedBB)

        if (self.predictionsMade >= self.uploadInterval):
            print("About to update firebase")

            self.fb.addData(self.dogroll.getAverage(), self.catroll.getAverage(), self.personroll.getAverage())

            self.predictionsMade = 0

        return results