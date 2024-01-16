# import torch
from RollingAverage import RollingAverage

class Analytics():
    def __init__(self, model, firebase, uploadInterval=180):
        self.model = model
        self.predictionsMade = 0
        self.uploadInterval = uploadInterval

        self.dogroll = RollingAverage(uploadInterval) 
        self.catroll = RollingAverage(uploadInterval) 
        self.personroll = RollingAverage(uploadInterval) 

        self.fb = firebase

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
        # x, y, width, height = tuple(box)

        x, y, width, height = tuple(box)
        xc = x + (width/2)
        yc = y + (height/2)

        return [xc, yc]

    def _velocity(self, curr_pred, spelledOutLabel):
        # past_pred contains the past class and past bb center
        
        distanceDifference = 0

        currCenter = curr_pred[spelledOutLabel]

        if spelledOutLabel in self.past_pred:
            pastCenter = self.past_pred[spelledOutLabel]

            distanceDifference = abs(currCenter[0] - pastCenter[0]) + abs(currCenter[1] - pastCenter[1])

        return distanceDifference


    # def _labelCheckToIncrementHigherVersion(self, spelledOutLabel, distance_diff):
    #     # Requires python 3.10 and up
    #     # Based off class update rolling average
    #     match spelledOutLabel:
    #         case "dog":
    #             self.dogroll.addValue(distance_diff)
    #             dogCount += 1
    #         case "cat":
    #             self.catroll.addValue(distance_diff)
    #             catCount += 1
    #         case "person":
    #             self.personroll.addValue(distance_diff)
    #             personCount += 1
    #         case _:
    #             print("No accepted class found")

    def _labelCheckToIncrement(self, spelledOutLabel, distance_diff, dogCount, catCount, personCount):
        # Based off class update rolling average
        if spelledOutLabel == "dog":
            self.dogroll.addValue(distance_diff)
            dogCount += 1
        elif spelledOutLabel == "cat":
            self.catroll.addValue(distance_diff)
            catCount += 1
        elif spelledOutLabel == "person":
            self.personroll.addValue(distance_diff)
            personCount += 1
        else:
            print("No accepted class found")

        return dogCount, catCount, personCount

    def analytics(self, results):

        # break results to filter by class
        labels = []
        # labels_id = []
        scores = []
        boxes =[]
        for item in results["predictions"]:
            labels.append(item["class"])
            # labels_id.append(item["class_id"])
            scores.append(item["confidence"])
            boxes.append([item['x'],item['y'],item['width'],item['height']])

        # Count set so if none detected activity of zero will be placed
        dogCount = 0
        catCount = 0
        personCount = 0

        # scores_tensor = torch.tensor(scores)
        # labels_id_tensor = torch.tensor(labels_id)
        # boxes_tensor = torch.tensor(boxes)
        # passedArray = torch.zeros(scores_tensor.size(), dtype=torch.bool)
        # passedBB = torch.zeros(boxes_tensor.size(), dtype=torch.bool)

        iter = 0
        for score, label, box in zip(scores, labels, boxes):

            spelledOutLabel = label
            if self._classFilter(spelledOutLabel):
                # passedArray[iter] = True
                # passedBB[iter,:] = True

                bb_center = self._centerpoint(box)
                pred_center = {spelledOutLabel: bb_center}

                if self.past_pred[spelledOutLabel] is not None:
                    distance_diff = self._velocity(pred_center, spelledOutLabel)

                    if (distance_diff > 0):

                        # self._labelCheckToIncrementHigherVersion(spelledOutLabel, distance_diff)
                        dogCount, catCount, personCount = self._labelCheckToIncrement(spelledOutLabel, distance_diff, dogCount, catCount, personCount)

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

        # results["scores"] = torch.masked_select(scores_tensor,passedArray)
        # results["labels"] = torch.masked_select(labels_id_tensor,passedArray)
        # results["boxes"] = torch.masked_select(boxes_tensor,passedBB)

        if (self.predictionsMade >= self.uploadInterval):

            self.fb.addData(self.dogroll.getAverage(), self.catroll.getAverage(), self.personroll.getAverage())

            self.predictionsMade = 0

        # return results