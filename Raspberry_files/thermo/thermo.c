/* simple program to control temperature inside the incubator
maxTemp an minTemp provide the range of allowed temp.
Relay is closed if temp is lower than minTemp and 
openned when higher tan maxTemp

Temperature Sensor is a Dallas 18B20 connected to GPIO4
Relay is connected to GPIO0

wiringPi lib and w1 module from Frank Buss (www.frank-buss.de)
*/

#include <wiringPi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sqlite3.h>

#define maxTemp 37.1
#define minTemp 36.5


int main ()
{
	FILE *fp,*tempFile; 
	sqlite3 *db;
	int value, rc, intTemp;
	char fileText[50];
	char sql[50],sqlTemp[7];
	char *ptrTemp;
	float temp;
	
	int pin = 0;
	
	if (wiringPiSetup() == -1) {
		printf ("Error loading wiringPi library");
		exit(1);
		}

	pinMode (pin, OUTPUT);
	digitalWrite (pin,0);
	value=0;

	//if (rc)
	//	return(1);

	while (1){
		if((fp=fopen("/sys/bus/w1/devices/w1_bus_master1/28-000003e3fa74/w1_slave","r")) == NULL){
			printf ("DS180  driver not loaded");
	 		exit (1);
			}
	 	fgets(fileText, 50, fp);
		//printf ("\n%s",fileText);
		fgets(fileText, 50, fp);
		//printf ("\n%s",fileText);
	 	ptrTemp = strrchr(fileText,'t');
		if (ptrTemp != NULL){
			ptrTemp+=2;
			temp=atoi(ptrTemp);
			temp/=1000;
			if((tempFile=fopen("/home/pi/test/thermostate/lastTemp.txt","w")) != NULL){
				fprintf(tempFile, "%f", temp);
				fclose(tempFile);
				}
			strcpy(sql,"INSERT INTO \"LOG\" (\"TEMP_LOG\", \"STATUS_LOG\") VALUES (");
			strncpy(sqlTemp,ptrTemp,5);
			for (intTemp=5;intTemp>2;intTemp--)
				sqlTemp[intTemp]=sqlTemp[intTemp-1];
			sqlTemp[6]='\0';
			sqlTemp[2]='.';
			strcat(sql,sqlTemp);
			strcpy(sqlTemp,", ");
			strcat(sql,sqlTemp);
			intTemp = strlen(sql);
			sql[intTemp] = value + 0x30;
			sql[intTemp+1]=')';
			sql[intTemp+2]=';';
			sql[intTemp+3]='\0';
			//strcpy(sqlTemp,")");
			//strcat(sql,sqlTemp);
//			intTemp=sqlite3_exec(db,"BEGIN IMMEDIATE TRANSACTION", NULL, 0, &ptrTemp);
			rc = sqlite3_open("/home/pi/test/thermostate/incubator.db", &db);
			intTemp=sqlite3_exec(db, sql, NULL, 0, &ptrTemp);
			if (intTemp != SQLITE_OK){
				printf("Error in Insert statement: \n%s\n%s.\n",sql,ptrTemp);
			}
			sqlite3_close(db);				
//			intTemp=sqlite3_exec(db,"COMMIT TRANSACTION", NULL, 0, &ptrTemp);
			//printf("%s\n",sql);
			//printf("temperatura=%f\n",temp);
			if ((temp < minTemp)&&(value==0)){
				digitalWrite(pin,1);
				value=1;
				//printf ("conectado\n");
			}
			if ((temp > maxTemp)&&(value==1)){
				digitalWrite(pin,0);
				value=0;
				//printf ("apagado\n");
			}
		}

        delay(14000);

        fclose(fp);

        }


}
