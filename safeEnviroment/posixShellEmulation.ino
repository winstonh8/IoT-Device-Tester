void setup()
{
    Serial.begin(115200);
    Serial.setTimeout(3);
    Serial.print("SIMPLY EMBEDDED POSIX SHELL\n"
                 "Try help to view available commands");
}

void loop()
{
    String recv;
    recv = Serial.readString();
    String echo = recv.substring(0, 4);
    if (echo == "echo")
    {
        recv.remove(0, 5);
        Serial.print(recv);
    }
}