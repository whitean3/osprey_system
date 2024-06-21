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
import pyOsprey_lib as OspreyLib
import queuepy
from pyOsprey_enumerations import OspreyEnums
import matplotlib.pyplot as plt


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


def detect_objects(identifier, image, model, cps):
    class_list = model.model.names

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

    # Saves cropped objects in output folder
    person_num = 0
    car_num = 0
    object_num = 0
    for detected_object in objects[3]:
        if objects[1][object_num] == 'car':
            car_num += 1
            object_img_name = 'car' + str(car_num) + '.png'
            cv2.imwrite(object_img_name, detected_object)
        if objects[1][object_num] == 'person':
            person_num += 1
            object_img_name = 'person' + str(person_num) + '.png'
            cv2.imwrite(object_img_name, detected_object)
        object_num += 1

    return {
        'Detector': identifier,
        'objects': objects[1],
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
        filename = "Detector " + detector.Name + " Background Spectrum"
        path = "Background Spectra/" + filename
        cv2.imwrite(path, plt.hist(detector.Background_SpectrumData.Spectrum))

    return


def detection_event(detector, background_cps, sn, model, cps):
    highest_cps = 0
    current_cps = 0
    event_duration = 0
    original_dir = os.getcwd()
    camera_link = "http://admin:Y%Lab2024@" + sn + "/cgi-bin/snapshot.cgi"
    feed = cv2.VideoCapture("http://admin:Y%Lab2024@10.0.0.118/cgi-bin/snapshot.cgi")
    highest_cps_frame = feed.read()
    print("Detector", sn, "high counts, initiating detection event.")
    detector.OspreyInstance.Acquisition_Start()

    while cps > 1.5 * background_cps:
        cps = detector.GetData_CountRate()
        print(cps)
        if cps > highest_cps:
            feed = cv2.VideoCapture("http://admin:Y%Lab2024@10.0.0.118/cgi-bin/snapshot.cgi")
            ret, highest_cps_frame = feed.read()
            highest_cps = cps
        event_duration += 1
        time.sleep(1)

    detector.OspreyInstance.Acquisition_Stop()
    event_spectrumData = detector.OspreyInstance.GetData_PHA()

    cv2.imwrite("Event Spectrum", plt.hist(event_spectrumData.Spectrum))
    print("Detection event over, analyzing highest count frame...")
    result = detect_objects(sn, highest_cps_frame, model, highest_cps)
    print("Image processed.")
    print("Objects detected in image:", result['objects'])
    print("Event duration:", event_duration, "s")
    print(original_dir)
    os.chdir(original_dir)
    return


# Creates Detector object for each detector in system
detectors = [Detector('A', '10.0.0.3', '10.0.0.118')]  # Detector('B', '10.0.1.5', '10.0.0.137')]


def main():
    model = YOLO('yolov8x.pt')

    diagnostics_ConnectionMethod = OspreyEnums.ConnectionMethod.Ethernet
    diagnostics_AcquireSpectrum = True
    diagnostics_LiveTime_sec = 5
    diagnostics_Histogram_enabled = True
    diagnostics_Histogram_bins = 48
    diagnostics_Histogram_height = 10
    diagnostics_Write_CSVs = False

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
    while True:
        highest_cps = 0
        # Read CPM value from nanoMCA
        for detector in detectors:
            cps = detector.OspreyInstance.GetData_CountRate()
            queuepy.Queue(detector.Bkg_counts, 20, cps)
            detector.background = sum(detector.Bkg_counts)/len(detector.Bkg_counts)
            print("Detector IP:", detector.IP, "Current count rate:", cps)
            if cps > 2 * detector.Background:
                detection_event(detector.OspreyInstance, detector.Background, detector.IP, model, cps)

            time.sleep(0.5)


if __name__ == "__main__":
    main()
