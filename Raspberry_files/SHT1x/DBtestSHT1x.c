// Compile with: gcc -o testSHT1x ./../bcm2835-1.3/src/bcm2835.c ./RPi_SHT1x.c testSHT1x.c

/*
Gustavo Martin

This is a derivative work based on
	Name:	Raspberry Pi SHT1x communication library.
	By:      John Burns (www.john.geek.nz)
	Date:    14 August 2012
	License: CC BY-SA v3.0 - http://creativecommons.org/licenses/by-sa/3.0/

This is a derivative work based on
	Name: Nice Guy SHT11 library
	By: Daesung Kim
	Date: 04/04/2011
	Source: http://www.theniceguy.net/2722

Dependencies:
	BCM2835 Raspberry Pi GPIO Library - http://www.open.com.au/mikem/bcm2835/

Sensor:
	Sensirion SHT11 Temperature and Humidity Sensor interfaced to Raspberry Pi GPIO port

SHT pins:
	1. GND  - Connected to GPIO Port P1-06 (Ground)
	2. DATA - Connected via a 10k pullup resistor to GPIO Port P1-01 (3V3 Power)
	2. DATA - Connected to GPIO Port P1-18 (GPIO 24)
	3. SCK  - Connected to GPIO Port P1-16 (GPIO 23)
	4. VDD  - Connected to GPIO Port P1-01 (3V3 Power)

Note:
	GPIO Pins can be changed in the Defines of RPi_SHT1x.h
*/

#include <bcm2835.h>
#include <stdio.h>
#include <stdlib.h>
#include "RPi_SHT1x.h"
#include <string.h>
#include <sqlite3.h>

#define maxTemp 37.75
#define minTemp 37.55
#define maxHumi 60.5
#define minHumi 55.5
	#define PIN RPI_GPIO_P1_12


void getTempAndHumidity(value *valor)
{
	unsigned char noError = 1;  
	value humi_val,temp_val;
	int error = 0; 
	
	
	// Wait at least 11ms after power-up (chapter 3.1)
	delay(20); 
	
	// Set up the SHT1x Data and Clock Pins
	SHT1x_InitPins();
	
	// Reset the SHT1x
	SHT1x_Reset();
	
	// Request Temperature measurement
	noError = SHT1x_Measure_Start( SHT1xMeaT );
	if (!noError) {
		error = 1;
		}
		
	// Read Temperature measurement
	if (error == 0)
	{
		noError = SHT1x_Get_Measure_Value( (unsigned short int*) &temp_val.i );
		if (!noError) {
			error = 2;
			}
		if (error == 0)
		{
			// Request Humidity Measurement
			noError = SHT1x_Measure_Start( SHT1xMeaRh );
			if (!noError) {
				error = 3	;
				}
			if (error == 0)
			{	
				// Read Humidity measurement
				noError = SHT1x_Get_Measure_Value( (unsigned short int*) &humi_val.i );
				if (!noError) {
					error = 4;
					}
			}
		}
	}
	if (error == 0)
	{
		// Convert intergers to float and calculate true values
		temp_val.f = (float)temp_val.i;
		humi_val.f = (float)humi_val.i;
		SHT1x_Calc(&humi_val.f, &temp_val.f);
	}
	else
		{
		temp_val.f = (float)error;
		humi_val.f = (float)100;
		}
		
	
	// Calculate Temperature and Humidity

	//Print the Temperature to the console
	//printf("Temperature: %0.2f%cC\n",temp_val.f,0x00B0);

	//Print the Humidity to the console
	//printf("Humidity: %0.2f%%\n",humi_val.f);
	valor[0] = temp_val;
	valor[1] = humi_val;

}

int main ()
{
	FILE *tempFile; 
	sqlite3 *db;
	value lecturas[2];
	int contar;
	//Initialise the Raspberry Pi GPIO
	int rc, intTemp;
	char sql[100],sqlTemp[20];
	time_t tiempo; 
	char *ptrTemp;

	if(!bcm2835_init())
		return 1;
	
	bcm2835_gpio_fsel(PIN, BCM2835_GPIO_FSEL_OUTP);
	contar = 0;
	while (1)
	{
		getTempAndHumidity(lecturas);
		printf ("temperatura: %f; humedad: %f\n", lecturas[0].f, lecturas[1].f);	
		if (lecturas[1].f < minHumi)
			bcm2835_gpio_write(PIN, HIGH);
		if (lecturas[1].f > maxHumi)
			bcm2835_gpio_write(PIN, LOW);

		if((tempFile=fopen("/home/pi/test/sht1x/lastTemp.txt","w")) != NULL){
				fprintf(tempFile, "%f", lecturas[0].f);
				fclose(tempFile);
				}

		if((tempFile=fopen("/home/pi/test/sht1x/lastHumi.txt","w")) != NULL){
				fprintf(tempFile, "%f", lecturas[1].f);
				fclose(tempFile);
				}
		if (contar++ == 6)
		{
			strcpy(sql,"INSERT INTO \"READ\" (\"date\", \"temp\", \"humi\") VALUES (CURRENT_TIMESTAMP, ");
			sprintf(sqlTemp, "%f", lecturas[0].f);
			strcat(sql, sqlTemp);
			strcpy(sqlTemp,", ");
			strcat(sql,sqlTemp);
			sprintf(sqlTemp, "%f", lecturas[1].f);
			strcat(sql, sqlTemp);
			strcpy(sqlTemp,"); ");
			strcat(sql,sqlTemp);
			rc = sqlite3_open("/home/pi/test/thermo.db", &db);
			intTemp=sqlite3_exec(db, sql, NULL, 0, &ptrTemp);
				if (intTemp != SQLITE_OK){
					printf("Error in Insert statement: \n%s\n%s.\n",sql,ptrTemp);
				}
				sqlite3_close(db);				
			contar = 0;
		}
		//printf ("%s\n\n", sql);


		bcm2835_delay(10000);

	}

	bcm2835_close();
	return 1;
}
