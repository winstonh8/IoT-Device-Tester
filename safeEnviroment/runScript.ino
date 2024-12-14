/**
 * \file boot_args_parser.c
 * \Sends boot arguments over a serial port for parsing
 *
 * Copyright (c) 2020 Simply Embedded Inc.
 * All Rights Reserved.
 */
String testList = "UNIT TEST LIST\n"
                  "Test 1: sec_element_init\n"
                  "Test 2: sec_element_random_num_gen_test\n"
                  "Test 3: json_decode_id_unit_test\n"
                  "Test 4: json_decode_nested_object_test\n"
                  "Test 5: json_encode_decode_string_property\n"
                  "Test 6: json_encode_decode_int_property\n"
                  "Test 7: json_encode_decode_multiple_properties\n"
                  "Test 8: json_encode_decode_object\n"
                  "Test 9: All Tests";
void setup()
{
  Serial.begin(115200);
  // Serial.setTimeout(3);
  Serial.print("Sense Tech Lanyard Application v2.1.0 "
               "SDK Version: SIM-NONE "
               "FreeRTOS Version: V10.3.1 "
               "LVGL Version: 7.9.0 "
               "LWIP Version: 2.2.0d "
               "MBED TLS Version: 2.16.6 "
               "CRYPTOAUTHLIB Version: 3.3.2 "
               "Bootargs: 2"
               "Initializing Watchdog "
               "Serial number: 0000-0101-00000000 "
               "IOT hubname: IOTHub-clrjgnjed5mjk.azure-devices.net "
               "Profile ID: 0 ");
}

void loop()
{
  String recv;
  while (!Serial.available())
    ;
  recv = Serial.readString();
  if (recv == "--tests")
  {
    Serial.print(testList);
  }
  else if (recv == "--exit")
  {
    Serial.print("closing port");
    Serial.end();
  }
}