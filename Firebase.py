import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

class Firebase():
    def __init__(self, production=True):

        if production:
            # Verify with firebase docs
            self.app = firebase_admin.initialize_app()
            self.db = firestore.client()
            self.past_streamDoc = ""
        else:
            # Use a service account.
            cred = credentials.Certificate('YOUR_SERVICE_ACCOUNT_KEY_JSON_FROM_FIREBASE')
            self.app = firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.past_streamDoc = ""


    def _addUID(self, uid):
        self.uid = uid

    def addData(self, dogAvg, catAvg, personAvg):


        activityData = {
        "dog": dogAvg,
        "cat": catAvg,
        "person": personAvg,
        "timestamp": firestore.SERVER_TIMESTAMP,
        }
        self.db.collection("users").document(self.uid).collection("activity").add(activityData)

    def streamingListen(self):
        found_stream = False
        
        while not found_stream:
            docs = (
                self.db.collection("streams")
                .where(filter=FieldFilter("status", "==", "streaming"))
                .stream()
            )

            for doc in docs:
                print(f"{doc.id} => {doc.to_dict()}")
                doc_dict = doc.to_dict()
                if len(doc_dict) > 0:
                    self.streamDoc = doc.id
                    source = doc_dict["url"]
                    user = doc_dict["user"]
                    found_stream = True
                    source = source.replace("\n", "")
                    user = user.replace("\n", "")
                    self._addUID(user)

        return source, user

    def updateStreamAsProcessing(self):
        stream_ref = self.db.collection("streams").document(self.streamDoc)

        stream_ref.update({"status":"processing"})

    def updateStreamBackToStreaming(self):
        # Failure in ML Server Doesn't mean stream failed, allow media server and camera to determine
        stream_ref = self.db.collection("streams").document(self.streamDoc)

        stream_ref.update({"status":"streaming"})

        self.past_streamDoc = self.streamDoc

    
    def updateStreamAsBroken(self):
        stream_ref = self.db.collection("streams").document(self.streamDoc)

        # if equals past stream then it is stuck looping on broken stream
        # else the stream might still be good just ML server crashed
        if self.past_streamDoc == self.streamDoc:
            # Set stream to status broken
            stream_ref.update({"status":"broken"})
        else:
            stream_ref.update({"status":"streaming"})

        self.past_streamDoc = self.streamDoc

    
