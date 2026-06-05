# Frontend UI/UX Design Specification
**Project:** Feynman Digital Twin Interface

## 1. Core Visual Theme & Aesthetic
The UI will reject standard, monotonous chatbot designs. Instead, it will adopt a high-end, **Industrial Sci-Fi** aesthetic—reminiscent of 1960s Los Alamos or Caltech mainframe terminals, modernized with sleek, smooth interactions. The color palette will feature muted slate greys, deep terminal blues, and subtle amber/orange highlights.

## 2. Dynamic Background & Scrollytelling
- **The Visual Canvas:** The background will not be static. We will utilize an `ImageSequence` architecture (via Vite and React) to create a dynamic, movable background. 
- **Composition:** 10 to 15 iconic, high-quality images of Richard Feynman (playing bongos, at the chalkboard, in lectures) will be alpha-composited into the background.
- **Behavior:** As the user scrolls through the timeline or interacts with the chat, the background images subtly parallax and transition. The images will have a gentle opacity/blur filter applied so they remain beautiful and dynamic, but never too dark or visually overwhelming to read the text over them.

## 3. The Timeline Component
- **Structure:** A central visual spine on the side of the screen.
- **Function:** Tracks the conversation visually, but also plots Richard's actual life events (Timeline Aware bonus) [cite: 75]. 
- **User Node (Friend):** A clean, circular photo/avatar of the user (the "friend") is anchored at the top or bottom of the timeline.
- **Feynman Node:** A corresponding photo of Richard is positioned below or opposite the user, visually representing the connection and flow of data between the two.

## 4. The Messaging Interface (WhatsApp/iMessage Style)
- **Rejection of the "Chat Box":** There will be no generic square text box at the bottom of the screen. 
- **Texting UX:** The interface will mimic a fluid messaging app. Messages appear as sleek, floating bubbles with subtle drop shadows.
- **Natural Interaction:** The input area will be a seamlessly integrated glass-morphic pill at the bottom. When the user types, it feels conversational, not like issuing commands to an AI.

## 5. Live Avatar Presence & Voice Integration
- **Character Animation:** On the "Feynman" side of the chat, there will be an interactive presence. When the Gemini API is generating a response, an animation shows Richard "thinking" (e.g., a subtle chalk-dust animation or a dynamic waveform).
- **Audio Mimicry System:** - The UI will include an integrated audio player in his message bubbles.
  - **Real-Time Voice:** The backend utilizes an acoustic voice-cloning TTS model (trained via isolated spectrogram analysis of his YouTube interviews). This secures the voice interaction bonus [cite: 73].
  - **Playback:** When a text response arrives, the UI automatically triggers the `.wav` audio stream. The user hears Richard's distinct Far Rockaway accent, complete with pauses and rhythm, natively within the web app.
