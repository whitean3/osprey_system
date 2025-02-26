from os import mkdir

import cv2
import os
import torch
import csv
from ultralytics import YOLO
import numpy as np
import time
from datetime import date, datetime
from PIL import Image
import random

from ultralytics.utils import imwrite

import pyOsprey_lib as OspreyLib
import queuepy

from ObjectRecognition import object_recognition
from pyOsprey_enumerations import OspreyEnums
import matplotlib.pyplot as plt
import ObjectRecognition
import Response_Correlation


class Detector:
    """
    Object that contains information relevant to each Detector/camera pair
    """
    def __init__(self, name, detectorIP, camIP):
        self.Background = 0
        self.Name = name
        self.IP = detectorIP
        self.CamIP = camIP
        self.Bkg_counts = []
        self.OspreyInstance = OspreyLib.Osprey()
        self.Background_SpectrumData = OspreyLib.SpectrumData


def detect_objects(identifier, image, model, cps, frames):
    class_list = model.model.names
    objects_of_interest = ['car', 'truck', 'person']
    # Perform object detection

    results = model(image)

    # Process the detections

    objects = get_objects(image, results[0], class_list)
    image_objects = objects[0]

    current_time = datetime.now().strftime("%y-%m-%d-%Hh%Mm%Ss")

    # Creates an output folder with detector number and current date/time in name
    output_folder_path = 'detector_' + str(identifier) + '_' + current_time
    path = os.path.join(os.getcwd(), output_folder_path)
    os.mkdir(path)
    os.chdir(path)
    # Labeling image
    text = "Detector: " + str(identifier) + " Max Counts:" + str(cps)
    cv2.putText(image_objects, text, (15, 15)
                , cv2.FONT_HERSHEY_SIMPLEX, 0.75
                , (0, 0, 255), 2, cv2.LINE_AA)
    # Saves full image with detection boxes and classes
    cv2.imwrite(output_folder_path+'.png', image_objects)
    c = 0
    for im in frames:

        cv2.imwrite(output_folder_path+' ' + str(c) + '.png', im)
        c += 1

    # Saves cropped objects in output folder
    person_num = 0
    car_num = 0
    object_num = 0
    image_paths = []
    for detected_object in objects[3]:
        for object_type in objects_of_interest:
            if objects[1][object_num] == object_type:
                object_img_name = object_type + str(object_num) + '.png'
                cv2.imwrite(object_img_name, detected_object)
                image_paths.append(object_img_name)



        object_num += 1

    return {
        'Detector': identifier,
        'objects': objects[1],
        'image paths': image_paths,
        'time': current_time,
    }


def get_objects(img, result, class_list):
    regions = []
    # Get information from result
    xyxy = result.boxes.xyxy.numpy()
    confidence = result.boxes.conf.numpy()
    class_id = result.boxes.cls.numpy().astype(int)
    # Get Class name
    class_name = [class_list[x] for x in class_id]
    # Pack together for easy use
    sum_output = list(zip(class_name, confidence,xyxy))
    # Copy image, in case that we need original image for something
    out_image = img.copy()
    for run_output in sum_output:
        # Unpack
        label, con, box = run_output
        # Choose color
        box_color = (0, 0, 255)
        text_color = (0,0,0)
        # Draw object box
        first_half_box = (int(box[0]),int(box[1]))
        second_half_box = (int(box[2]),int(box[3]))
        cv2.rectangle(out_image, first_half_box, second_half_box, box_color, 2)
        # Create text
        text_print = '{label} {con:.2f}'.format(label=label, con=con)
        # Locate text position
        text_location = (int(box[0]), int(box[1] - 10))
        # Put text
        cv2.putText(out_image, text_print,text_location
                    , cv2.FONT_HERSHEY_SIMPLEX, 0.5
                    , text_color, 2, cv2.LINE_AA)
        regions.append(extract_object(img, box))

    return out_image, class_name, confidence, regions


def extract_object(image, box):
    # Extract the region specified by the bounding box
    x1, y1, x2, y2 = box
    region = image[int(y1):int(y2), int(x1):int(x2)]
    # Calculate the average color within the region
    average_color = np.mean(region, axis=(0, 1)).astype(int)

    return region


def initialize_background_reading(det):
    t = 10

    for detector in det:
        detector.Bkg_counts = [0]*t
        detector.OspreyInstance.Acquisition_Start()

    for c in range(0, t):
        for detector in det:
            cps = detector.OspreyInstance.GetData_CountRate()
            detector.Bkg_counts[c] = cps
        time.sleep(1)

    for detector in det:
        detector.Background = sum(detector.Bkg_counts) / t
        detector.OspreyInstance.Acquisition_Stop()
        detector.Background_SpectrumData = detector.OspreyInstance.GetData_PHA()
        filename = "Detector " + str(detector.Name) + " Background Spectrum.png"
        path = os.path.join(os.getcwd(), "Background Spectra\\")
        fig = plt.figure()
        plt.hist(detector.Background_SpectrumData.Spectrum, bins=1024)
        plt.savefig(path + filename)

    return


def detection_event(detector, background_cps, sn, model, cps, cam_ip):
    highest_cps = 0
    current_cps = 0
    event_duration = 0
    original_dir = os.getcwd()
    camera_link = "http://admin:Y%Lab2024@" + sn + "/cgi-bin/snapshot.cgi"
    feed = cv2.VideoCapture("http://admin:Y%Lab2024@" + cam_ip + "/cgi-bin/snapshot.cgi")
    highest_cps_frame = feed.read()
    print("Detector", sn, "high counts, initiating detection event.")
    frames = []
    detector.OspreyInstance.Acquisition_Start()

    while cps > 1.2 * background_cps:
        cps = detector.OspreyInstance.GetData_CountRate()
        print(cps)
        feed = cv2.VideoCapture("http://admin:Y%Lab2024@" + cam_ip + "/cgi-bin/snapshot.cgi")
        ret, event_frame = feed.read()
        frames.append(event_frame)
        if cps > highest_cps:
            highest_cps_frame = event_frame
            highest_cps = cps
        event_duration += 1
        time.sleep(0.25)

    detector.OspreyInstance.Acquisition_Stop()
    event_spectrumData = detector.OspreyInstance.GetData_PHA()

    print("Detection event over, analyzing highest count frame...")
    result = detect_objects(sn, highest_cps_frame, model, highest_cps, frames)
    print("Image processed.")
    print("Objects detected in image:", result['objects'])
    print("Event duration:", event_duration, "s")

    filename = "Detector " + str(detector.Name) + " Event Spectrum.png"
    fig = plt.figure()
    plt.hist(detector.Background_SpectrumData.Spectrum, bins=1024)
    plt.savefig(filename)

    print(original_dir)
    os.chdir(original_dir)
    return result, highest_cps


# Creates Detector object for each detector in system
detectors = [Detector('A', '10.0.0.3', '10.0.0.118')]  # Detector('B', '10.0.1.5', '10.0.0.137')]


def save_pairs(pairs, result1, result2):
    for pair in pairs:
        if pair.Similarity >= 0.5:
            dual_event_folder_name = ("Detector1:" + result1['Detector'] + "_Time:" +
                                      result1['time'] + "_Detector2:" + result2['Detector']
                                      + "_Time:" + result2['time'])
            dual_event_path = os.path.join(os.getcwd(), dual_event_folder_name)
            os.mkdir(dual_event_path)
            os.chdir(dual_event_path)
            np.savetxt(pair.Name, pair.Similarity, delimiter=",")

    return


def main():
    model = YOLO('yolov8x.pt')
    diagnostics_ConnectionMethod = OspreyEnums.ConnectionMethod.Ethernet
    diagnostics_AcquireSpectrum = True
    diagnostics_LiveTime_sec = 5
    diagnostics_Histogram_enabled = True
    diagnostics_Histogram_bins = 48
    diagnostics_Histogram_height = 10
    diagnostics_Write_CSVs = False

    event_count = 0

    for detector in detectors:      # Detector and Camera connection
        if detector.OspreyInstance.Connect(method=diagnostics_ConnectionMethod):
            print("Osprey", detector.Name, "successfully Connected")
        else:
            print("Osprey", detector.Name, "failed to connect")

        print("Connecting Cameras...")
        camera_link = "http://admin:Y%Lab2024@" + detector.CamIP + "/cgi-bin/snapshot.cgi"
        feed = cv2.VideoCapture(camera_link)
        ret, highest_cps_frame = feed.read()
        if ret:
            print("Camera ", detector.Name, " Connected.")
        else:
            print("Camera ", detector.Name, " unable to connect")

    print("Acquiring background counts...")
    initialize_background_reading(detectors)

    # Main loop
    try:
        while True:
            highest_cps = 0
            previous_highest_cps = 0
            # Read CPM value from nanoMCA
            for detector in detectors:
                cps = detector.OspreyInstance.GetData_CountRate()
                queuepy.Queue(detector.Bkg_counts, 20, cps)
                detector.background = sum(detector.Bkg_counts)/len(detector.Bkg_counts)
                print("Detector IP:", detector.IP, "Current count rate:", cps)
                if cps > 1.5 * detector.Background:
                    if event_count >= 1:
                        result1 = result
                    event_count += 1
                    result, highest_cps = detection_event(detector, detector.Background, detector.IP, model, cps,
                                    detector.CamIP)
                    if event_count > 1:
                        dual_event_pairs =  object_recognition(result1, result, highest_cps, previous_highest_cps)
                        save_pairs(dual_event_pairs, result1, result)
                    previous_highest_cps = highest_cps

                print(detector.background)
            time.sleep(0.25)
    except KeyboardInterrupt:
        for detector in detectors:
            detector.OspreyInstance.Disconnect()


if __name__ == "__main__":
    main()
