# DCPT : **A Multi-Modal Dataset of Drivers' Cognitive and Physical States in L3 Takeover Scenarios**

## Overview

This repository contains a specialized dataset of driver takeover responses in automated driving scenarios, including upper-body video,first-person view videos, eye-tracking and head motion data recordings. 

Participants in this dataset were engaged in a range of non-driving related tasks (NDRTs) during automated driving to simulate real-world distractions. These tasks were carefully designed to reflect common in-vehicle behaviors and are labeled in the filenames using task IDs.

The task types and their definitions are listed below:

- **1. No task**: Observing road conditions or the surrounding environment.
- **2. Watching video**: Watching videos on the central stack screen.
- **3. Playing game**: Playing games on a smartphone or iPad.
- **4. Messaging**: Text chatting with the experimenter via WeChat.
- **5. Phone call**: Conversing with the experimenter over the phone.
- **6. Listening to radio**: Listening to audio broadcasts on audio devices.
- **7. Reading**: Reading provided materials.
- **8. Eating**: Consuming snacks provided during the session.
- **9. Chatting with passenger**: Talking with the experimenter seated in the passenger seat.

Each driving session began with a period of automated driving while the participant engaged in one of the above tasks. A takeover request (TOR) was issued at a random time point, prompting the participant to resume control of the vehicle. Sensor data and video recordings from the moments leading up to this event were captured and organized accordingly.

In this updated version, we added the `Mapped_fixation/` folder containing fixation data projected onto the simulator scene to make the dataset applicable to a broader range of research scenarios, such as analyzing drivers’ gaze regions during takeover.

## Dataset Structure

The repository is organized into the following main folders:

- Upper_body_video_01/to Upper_body_video_09/: Contains upper body video recordings from nine separate tasks
- `First_person_view_video/`: Contains First-person view video recordings of participants
- `Eye-tracking&head motion data/`: Contains eye movement&head motion data
- `Mapped_fixation/`: Contains fixation data mapped onto the simulator scene snapshot (`Scene_Snapshot.jpg`)


### Root Directory Files

- `Takeover-Time.xlsx`: Records takeover times for each experimental trial
- `information.xlsx`: Contains demographic information of all participants
- `Scene_Snapshot.jpg`: A reference image of the simulator scene used for mapping gaze fixations
- README.md: Provides an overview of the dataset structure and contents

### Upper body video data

#### Naming Convention

Upper body video files follow the naming pattern:

`<NDRT>_P<Person>_<Date>_<Hour>_<Minute>_<Takeover Time>`

Where:

- `NDRT`: Non-driving related task ID (refer to Table II in our research paper)
- `Person`: Participant ID
- `Date`: Recording date in YYYYMMDD format
- `Hour`: Recording start hour in HH format
- `Minute`: Recording start minute in MM format
- `Takeover Time`: Takeover time in 0.1s units

#### Description

- 10-second clips before the takeover request was issued
- Resolution: 1920 x 1080 pixels

### First person view video data

#### Naming Convention

First person view video files follow the naming pattern:

`<NDRT>_P<Person>_<Date>_<Hour>_<Minute>_<Takeover Time>`

Where:

- `NDRT`: Non-driving related task ID (refer to Table II in our research paper)
- `Person`: Participant ID
- `Date`: Recording date in YYYYMMDD format
- `Hour`: Recording start hour in HH format
- `Minute`: Recording start minute in MM format
- `Takeover Time`: Takeover time in 0.1s units

#### Description

- 10-second clips before the takeover request was issued
- Resolution: 1280 x 720 pixels
- The task of "Messaging" in the dataset has been subjected to blurring processing to protect relevant information

### Eye-tracking&head motion data

#### Naming Convention

Eye-tracking&head motion files follow the naming pattern:

`<NDRT>_P<Person>_<Date>_<Hour>_<Minute>_<Takeover Time>`

Where:

- `NDRT`: Non-driving related task ID (refer to Table II in our research paper)
- `Person`: Participant ID
- `Date`: Recording date in YYYYMMDD format
- `Hour`: Recording start hour in HH format
- `Minute`: Recording start minute in MM format
- `Takeover Time`: Takeover time in 0.1s units

Missing data is denoted by an empty cell. The data starts 30 seconds prior to the takeover request.

#### Description

- Format: Excel spreadsheets

- Collected by Tobii Pro Glasses 2

- Each file includes the following information:

  **Eye-tracking data:**

  - Recording timestamp(Timestamp counted from the start of the recording in milliseconds)
  - Sensor(The identifier of the sensor capturing data)
  - Recording Fixation filter name(The name of the Fixation filter applied on the Recording eye tracking data in the export)
  - Event(Name of automatically or manually logged event)
  - Gaze point X, Y (averaged left and right eye gaze point in pixel)
  - Gaze point 3D X, Y, Z (averaged Gaze 3D position in pixel)
  - Gaze direction left/right X, Y, Z (Gaze 3D position in pixel)
  - Pupil position left/right X, Y, Z (Pupil 3D position in mm)
  - Pupil diameter left/right (Estimated size of pupil in mm)
  - Validity left,right(Indicates if the eyes have been correctly identified)
  - Eye movement type(Type of eye movement classified by the fixation filter)
  - Gaze event duration(The duration of the currently active eye movement in milliseconds)
  - Eye movement type index(Count is an auto-increment number for each eye movement type)
  - Fixation point X, Y (Horizontal and vertical coordinate of the averaged gaze point for both eyes in pixel)
  
  **Head motion data:**
  
  - Gyroscope X, Y, Z (angular velocity in deg/s)
  
  - Accelerometer X, Y, Z (linear acceleration in m/s²)
  
    

### Mapped fixation data

#### Naming Convention

Mapped fixation files follow the naming pattern:

`<NDRT>_P<Person>_<Date>_<Hour>_<Minute>_<Takeover Time>`

Where:

- `NDRT`: Non-driving related task ID (refer to Table II in our research paper)
- `Person`: Participant ID
- `Date`: Recording date in YYYYMMDD format
- `Hour`: Recording start hour in HH format
- `Minute`: Recording start minute in MM format
- `Takeover Time`: Takeover time in 0.1s units

Missing data is denoted by an empty cell. The data covers fixation events recorded within 5 seconds before and after the takeover request.

#### Description

- Two new columns are added to indicate the mapped fixation coordinates on the scene image:

    - Mapped fixation X – the horizontal pixel coordinate of the fixation point on the scene snapshot  
    - Mapped fixation Y – the vertical pixel coordinate of the fixation point on the scene snapshot

    
