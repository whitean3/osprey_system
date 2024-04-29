import cv2
import os
import torch
import csv
from ultralytics import YOLO
import numpy as np
import time
import serial
from datetime import date, datetime
from scipy.spatial import KDTree
from PIL import Image
from pyNanoMCA_lib import NanoMCA
import pyNanoMCA_MultiAcq as Multi
import random
import pyOsprey_lib
from pyOsprey_enumerations import OspreyEnums


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
    path = os.path.join(os.getcwd(),output_folder_path)
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


def initialize_background_reading(detector):
    total_counts = 0
    t = 10

    for c in range(0, t):
        total_counts += detector.GetData_CountRate()
        time.sleep(1)

    return total_counts/t


def detection_event(detector, feed, background_cps, sn, model, cps):
    highest_cps = 0
    current_cps = 0
    event_duration = 0
    original_dir = os.getcwd()

    print("Detector", sn, "high counts, initiating detection event.")
    ret, highest_cps_frame = feed.read()
    while cps > 1.5 * background_cps:
        cps = detector.GetData_CountRate()
        print(cps)
        if cps > highest_cps:
            ret, highest_cps_frame = feed.read()
            highest_cps = cps
        event_duration += 1
        time.sleep(1)
    print("Detection event over, analyzing highest count frame...")
    result = detect_objects(sn, highest_cps_frame, model, highest_cps)
    print("Image processed.")
    print("Objects detected in image:", result['objects'])
    print("Event duration:", event_duration, "s")
    print(original_dir)
    os.chdir(original_dir)
    return


def main():
    model = YOLO('yolov8x.pt')
    osprey = pyOsprey_lib.Osprey()

    diagnostics_ConnectionMethod = OspreyEnums.ConnectionMethod.USB

    diagnostics_IP_Override = '10.0.1.4', '10.0.1.5'

    diagnostics_EnableMassStorage = False
    diagnostics_EnableTFTP = False
    diagnostics_DisableTFTP = False
    diagnostics_FirmwareUpdate = False
    diagnostics_AcquireSpectrum = True
    diagnostics_LiveTime_sec = 5
    diagnostics_Histogram_enabled = True
    diagnostics_Histogram_bins = 48
    diagnostics_Histogram_height = 10
    diagnostics_Write_CSVs = False

    for ip in diagnostics_IP_Override:

        if osprey.Connect(method=diagnostics_ConnectionMethod, ip_address=ip):

            # Enable TFTP server?
            if diagnostics_EnableTFTP:
                osprey.TFTP_Enable()

            # Disable TFTP server?
            if diagnostics_DisableTFTP:
                osprey.TFTP_Disable()

            # Get status of TFTP server
            tftpStatus = osprey.TFTP_Status()
            print("TFTP server enabled?: " + str(tftpStatus))

            # Enter mass storage mode?
            if diagnostics_EnableMassStorage:
                osprey.MassStorageMode_Enable()

            # Perform firmware update?
            if diagnostics_FirmwareUpdate:
                try:
                    if osprey.Connected:
                        print("Performing firmware update...")
                        osprey.DTB.control(31, input)
                    else:  # Not connected
                        print("*** ERROR *** Cannot perform firmware update -- not connected!")
                except Exception as e:
                    print("*** ERROR *** Failed to perform firmware update on device")
                    print(str(e))

    print("Acquiring background counts...")
    background_cps = initialize_background_reading(osprey)
    print("Background cps:", background_cps)

    print("Connecting Camera...")
    import cv2
    import numpy as np

    feed1 = cv2.VideoCapture("rtsp://admin:Y%Lab2024@10.0.0.119/cam/realmonitor?channel=1&subtype=0")
    ret, highest_cps_frame = feed1.read()
    print("Camera Connected.")

    # Main loop
    while True:
        highest_cps = 0
        # Read CPM value from nanoMCA
        nD = 0
        for ip in diagnostics_IP_Override:
            cps = osprey.GetData_CountRate()
            print("Detector IP:", ip, "Current count rate:", cps)
            if cps > 2*background_cps:
                detection_event(osprey, feed1, background_cps, diagnostics_IP_Override, model, cps)
                nD += 1

            time.sleep(1)


if __name__ == "__main__":
    main()
