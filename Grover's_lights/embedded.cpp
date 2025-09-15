const int q1 = 13;
const int q2 = 12;
const int q3 = 8;
const int q4 = 4;

const int n = 4;
const int ledPins[n] = {q1, q2, q3, q4};

void setup() {
  Serial.begin(9600);
  for(int i=0;i<n;i++){
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }
}

void display_state(int stateIndex){
  for(int i=0;i<n;i++){
    digitalWrite(ledPins[i], (i==stateIndex)? HIGH : LOW);
  }
}

void loop(){
  if(Serial.available()>0){
    int state = Serial.parseInt();
    if(state>=0 && state<n){
      display_state(state);
      delay(1000);
    }
  }
}
