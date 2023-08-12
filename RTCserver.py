import argparse
import asyncio
# import json
import logging
import os
import ssl
import uuid

import cv2
# from aiohttp import web
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from av import VideoFrame

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore_async

import threading

ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()
relay = MediaRelay()


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform

    async def recv(self):
        frame = await self.track.recv()

        if self.transform == "cartoon":
            img = frame.to_ndarray(format="bgr24")

            # prepare color
            img_color = cv2.pyrDown(cv2.pyrDown(img))
            for _ in range(6):
                img_color = cv2.bilateralFilter(img_color, 9, 9, 7)
            img_color = cv2.pyrUp(cv2.pyrUp(img_color))

            # prepare edges
            img_edges = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            img_edges = cv2.adaptiveThreshold(
                cv2.medianBlur(img_edges, 7),
                255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                9,
                2,
            )
            img_edges = cv2.cvtColor(img_edges, cv2.COLOR_GRAY2RGB)

            # combine color and edges
            img = cv2.bitwise_and(img_color, img_edges)

            # rebuild a VideoFrame, preserving timing information
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
        # elif self.transform == "edges":
        #     # perform edge detection
        #     img = frame.to_ndarray(format="bgr24")
        #     img = cv2.cvtColor(cv2.Canny(img, 100, 200), cv2.COLOR_GRAY2BGR)

        #     # rebuild a VideoFrame, preserving timing information
        #     new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        #     new_frame.pts = frame.pts
        #     new_frame.time_base = frame.time_base
        #     return new_frame
        else:
            return frame
        

async def firebase_init():

    # Use a service account.
    cred = credentials.Certificate('brightpaw-d6fd6-firebase-adminsdk-qqfyk-a545031d78.json')

    app = firebase_admin.initialize_app(cred)

    db = firestore_async.client()

    return app, db

async def offer(db, uid): #request

    # Receives SDP message, transform type
    # params = await request.json()

    # Create Peer Connection
    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    # Get ref's
    callDoc = db.collection("users",uid,"calls").document() # needs to create new call doc
    offerCandidates = db.collection(callDoc,"offerCandidates").document() # similar to above for new doc but in offerCandidates
    uidDoc = db.collection("users").document(uid)

    callUID = {
        "latestCall": callDoc.id
    }
    await uidDoc.update(callUID) # add latest call for go server to answer

    ## Setup event handler for onicecandidate
    # // Get candidates for caller, save to db
    # getOrCreatePeerConnection().onicecandidate = (event) => {
    #     // console.log("OnIceCandidate Triggered")
    #     // event.candidate && console.log(event.candidate.toJSON())
    #     event.candidate && setDoc(offerCandidates, event.candidate.toJSON() );
    # };
    # @pc.on("onIceCandidate")
    # def on_icecandidate(icecandidate):
    #     # add logic here to handle icecandidate
    #     # set setDoc of offerCandidates

    # Create RTC offer
    # offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    offerDescription = pc.createOffer()
    await pc.setLocalDescription(offerDescription)

    offer = {
        "sdp": offerDescription.sdp,
        "type": offerDescription.type,
    }

    # Update offer to firebase
    await callDoc.set({ offer })



    # # Create Peer Connection
    # pc = RTCPeerConnection()
    # pc_id = "PeerConnection(%s)" % uuid.uuid4()
    # pcs.add(pc)

    # def log_info(msg, *args):
    #     logger.info(pc_id + " " + msg, *args)

    # log_info("Created for %s", request.remote)

    # # prepare local media
    # if args.record_to:
    #     recorder = MediaRecorder(args.record_to)
    # else:
    #     recorder = MediaBlackhole()

    ## Setup event handler for onicecandidate
    # // Get candidates for caller, save to db
    # getOrCreatePeerConnection().onicecandidate = (event) => {
    #     // console.log("OnIceCandidate Triggered")
    #     // event.candidate && console.log(event.candidate.toJSON())
    #     event.candidate && setDoc(offerCandidates, event.candidate.toJSON() );
    # };
    # @pc.on("onIceCandidate")
    # def on_icecandidate(icecandidate):
    #     # add logic here to handle icecandidate
    #     # set setDoc of offerCandidates

    # @pc.on("datachannel")
    # def on_datachannel(channel):
    #     @channel.on("message")
    #     def on_message(message):
    #         if isinstance(message, str) and message.startswith("ping"):
    #             channel.send("pong" + message[4:])

    # @pc.on("connectionstatechange")
    # async def on_connectionstatechange():
    #     log_info("Connection state is %s", pc.connectionState)
    #     if pc.connectionState == "failed":
    #         await pc.close()
    #         pcs.discard(pc)

    # @pc.on("track")
    # def on_track(track):
    #     log_info("Track %s received", track.kind)

    #     # if track.kind == "audio":
    #         # pc.addTrack(player.audio)
    #         # recorder.addTrack(track)
    #     if track.kind == "video":
    #         pc.addTrack(
    #             VideoTransformTrack(
    #                 relay.subscribe(track), transform=params["video_transform"]
    #             )
    #         )
    #         # if args.record_to:
    #         #     recorder.addTrack(relay.subscribe(track))

    #     @track.on("ended")
    #     async def on_ended():
    #         log_info("Track %s ended", track.kind)
    #         # await recorder.stop()

    @pc.on("icecandidate")
    async def on_ice_candidate(candidate: RTCIceCandidate):
        if candidate:
            # Convert RTCIceCandidate to JSON format and set it using your setDoc function
            candidate_data = {
                "candidate": candidate.sdp,
                "sdpMid": candidate.sdp_mid,
                "sdpMLineIndex": candidate.sdp_mline_index
            }
            # setDoc(offerCandidates, candidate_data)
            offerCandidates.set(candidate_data)


    # Create an Event for notifying main thread.
    callback_done = threading.Event()
    # Create a callback on_snapshot function to capture changes
    def on_snapshot(doc_snapshot, changes, read_time):
        data = doc_snapshot.data()
        if (pc.__currentRemoteDescription):
            if "answer" in data:
                answerDescription = RTCSessionDescription(data.answer)
                print("answer is..")
                print(answerDescription)
                pc.setRemoteDescription(answerDescription)
                print("Answer has been received and set to rem. desc.")
        # for doc in doc_snapshot:
        #     print(f"Received document snapshot: {doc.id}")
        callback_done.set()

    # Listen for remote answer
    callDoc.on_snapshot(on_snapshot)

    # # handle offer
    # await pc.setRemoteDescription(offer)
    # # await recorder.start()


    # Create an Event for notifying main thread.
    query_done = threading.Event()
    # Create a callback on_snapshot function to capture changes
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == "ADDED":
                candidate = RTCIceCandidate(change.doc.data())
                pc.addIceCandidate(candidate=candidate)
        query_done.set()

    answerQueries = db.collection(callDoc,"answerCandidates").query()
    # When answered, add candidate to peer connection
    answerQueries.on_snapshot(on_snapshot)

    # # send answer
    # answer = await pc.createAnswer()
    # await pc.setLocalDescription(answer)

    ## Below dumps local description
    # return web.Response(
    #     content_type="application/json",
    #     text=json.dumps(
    #         {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    #     ),
    # )


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":

    uid = "RJ0pPZEpmqPdiwMNBsuErIKU8zI3" # hardcode uid
    app, db = firebase_init()
    offer(db,uid)

    # parser = argparse.ArgumentParser(
    #     description="WebRTC audio / video / data-channels demo"
    # )
    # parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    # parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    # parser.add_argument(
    #     "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    # )
    # parser.add_argument(
    #     "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    # )
    # parser.add_argument("--record-to", help="Write received media to a file."),
    # parser.add_argument("--verbose", "-v", action="count")
    # args = parser.parse_args()

    # if args.verbose:
    #     logging.basicConfig(level=logging.DEBUG)
    # else:
    #     logging.basicConfig(level=logging.INFO)

    # if args.cert_file:
    #     ssl_context = ssl.SSLContext()
    #     ssl_context.load_cert_chain(args.cert_file, args.key_file)
    # else:
    #     ssl_context = None

    # app = web.Application()
    # app.on_shutdown.append(on_shutdown)
    # app.router.add_get("/", index)
    # app.router.add_get("/client.js", javascript)
    # app.router.add_post("/offer", offer)
    # web.run_app(
    #     app, access_log=None, host=args.host, port=args.port, ssl_context=ssl_context
    # )
