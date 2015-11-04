package com.xflowresearch.nfv.testertool.ue.nas;

import java.io.IOException;
import java.util.Arrays;

import javax.xml.bind.DatatypeConverter;

import org.bouncycastle.crypto.BlockCipher;
import org.bouncycastle.crypto.CipherParameters;
import org.bouncycastle.crypto.DataLengthException;
import org.bouncycastle.crypto.params.KeyParameter;
import org.bouncycastle.util.encoders.Hex;
import org.bouncycastle.util.test.SimpleTestResult;
import com.xflowresearch.nfv.testertool.ue.nas.RijnImp;
public class Algo {

private byte [] key;
private byte [] OP;
BlockCipher Rij= new RijndaelEngine();	
RijnImp Imp= new RijnImp();

Algo (byte [] key ,byte [] OP)
{
	this.key =key;
	this.OP= OP;
	
}


public byte [] ComputeOPc( byte[] op_c ) //op_c should be 16 byte  array
{
	
byte i;
Imp.RijndaelEncrypt(key,OP , Rij);
for (i=0; i<16; i++)
op_c[i] ^= OP[i];
return op_c;

} /* end of function ComputeOPc */



void f2345(/*byte[]k,*/byte []rand,byte[] res, byte []ck, byte []ik, byte [] ak){
		
		byte [] op_c = new byte[16];   //16 elements
		byte [] temp = new byte[16]; //16 elem
		byte [] out =new byte[16];       //16 elem
		byte [] rijndaelInput = new byte[16]; //16 elements
		byte i;  
		
		
	  Imp.setRijEngine(key, Rij);
	  ComputeOPc(op_c);
	  
	  for (i=0; i<16; i++)
	  { rijndaelInput[i] = (byte) (rand[i] ^ op_c[i]);
	  }
	  temp=Imp.RijndaelEncrypt( key,rijndaelInput,Rij );
		  
		  
		  /* To obtain output block OUT2: XOR OPc and TEMP, *
		  * rotate by r2=0, and XOR on the constant c2 (which *
		  * is all zeroes except that the last bit is 1). */
		  
	   for (i=0; i<16; i++)
		  { 
		   rijndaelInput[i] = (byte) (temp[i] ^ op_c[i]);
		  }
		  rijndaelInput[15] ^= 1;
		  
		
		out=Imp.RijndaelEncrypt( key ,rijndaelInput, Rij );
		for (i=0; i<16; i++)
			 {
			 out[i] ^= op_c[i];
			 }
		
		for (i=0; i<8; i++)
			 {
			 res[i] = out[i+8];
			 }
		  for (i=0; i<6; i++)
			 {
			  ak[i] = out[i];
			 }
		  
		  
		  /* To obtain output block OUT3: XOR OPc and TEMP
		   rotate by r3=32, and XOR on the constant c3 (which 
	       is all zeroes except that the next to last bit is 1). */
				  
		  
		  for (i=0; i<16; i++)
		  {
			  		rijndaelInput[(i+12) % 16] = (byte) (temp[i] ^ op_c[i]);
		  }
		  
		   rijndaelInput[15] ^= 2;
		  
		   Imp.RijndaelEncrypt( key,rijndaelInput, Rij );
			
			for (i=0; i<16; i++)
			{
				out[i] ^= op_c[i];
			}
		  
			for (i=0; i<16; i++)
				{
				ck[i] = out[i];
				}
			
			/* To obtain output block OUT4: XOR OPc and TEMP, *
			* rotate by r4=64, and XOR on the constant c4 (which *
			* is all zeroes except that the 2nd from last bit is 1). */
			for (i=0; i<16; i++)
			
				{
				rijndaelInput[(i+8) % 16] = (byte) (temp[i] ^ op_c[i]);
				}
			
			rijndaelInput[15] ^= 4;
			
			Imp.RijndaelEncrypt( key,rijndaelInput, Rij);
			for (i=0; i<16; i++)
			{
				out[i] ^= op_c[i];
			}
			for (i=0; i<16; i++)
			{
				ik[i] = out[i];
			}
			//returns byte[] res, byte []ck, byte []ik, byte ak[6]	
}
	  
/*-------------------------------------------------------------------
* Algorithm f5*
*-------------------------------------------------------------------
*
* Takes key K and random challenge RAND, and returns resynch
* anonymity key AK.
*
*-----------------------------------------------------------------*/
	  
void f5star( /*byte [] k,*/ byte [] rand,byte [] ak )
{
	byte [] op_c = new byte[16];   //16 elements
	byte [] temp = new byte[16]; //16 elem
	byte [] out =new byte[16];       //16 elem
	byte [] rijndaelInput = new byte[16]; //16 elements
	byte i;  
	
	Imp.setRijEngine(key, Rij);  //this step also computes the working key for object Rij
	
	ComputeOPc(op_c);
	  
	  for (i=0; i<16; i++)
	  { rijndaelInput[i] = (byte) (rand[i] ^ op_c[i]);
	  }
	  temp=Imp.RijndaelEncrypt( key,rijndaelInput,Rij );
	
	  /* To obtain output block OUT5: XOR OPc and TEMP, *
	  * rotate by r5=96, and XOR on the constant c5 (which *
	  * is all zeroes except that the 3rd from last bit is 1). */
	  
	  for (i=0; i<16; i++)
	  {
		  rijndaelInput[(i+4) % 16] = (byte) (temp[i] ^ op_c[i]);
	  }
	  rijndaelInput[15] ^= 8;
	  
	  out =Imp.RijndaelEncrypt( key ,rijndaelInput, Rij );
	  for (i=0; i<16; i++)
	  
		  {
		  out[i] ^= op_c[i];
		  }
	  for (i=0; i<6; i++)
		  {
		  ak[i] = out[i];
		  }
	  
}




/*public static void main(String[] args) throws IOException{

String k= "465B5CE8B199B49FAA5F0A2EE238A6BC"; //key
String r="67c6697351ff4aec29cdbaabf2fbe346"; //rand
String op= "1918b840195c97017228127009ca194e";
byte []ck = new byte [16];
byte []ik= new byte [16];
byte []ak= new byte[6];
byte [] res = new byte [8];

//byte[] OP = {(byte)0x19,(byte)0x18,(byte)0xb8,(byte)0x40,(byte)0x19,(byte)0x5c,(byte)0x97,(byte)0x01,(byte)0x72,(byte)0x28,(byte)0x12,(byte)0x70,(byte)0x09,(byte)0xca,(byte)0x19,(byte)0x4e};
//byte [] key= {(byte)0x46, (byte) 0x5B,(byte) 0x5C,(byte) 0xE8,(byte) 0x99, (byte)0xB4, (byte)0x9F, (byte)68, (byte)126, (byte)213, (byte)16, (byte)115, (byte)68, (byte)217, (byte)58, (byte)108, (byte)56, (byte)218, (byte)5, (byte)78, (byte)28, (byte)128, (byte)113, (byte)208, (byte)61, (byte)56, (byte)10, (byte)87, (byte)187, (byte)162, (byte)233, (byte)38 };

byte[] key = DatatypeConverter.parseHexBinary(k);
byte [] rand =DatatypeConverter.parseHexBinary(r);
byte[] OP=DatatypeConverter.parseHexBinary(op);
//System.out.print(Byte.toString(key[5]));
//System.out.println(Arrays.toString(key[0]));
Algo obj =new Algo(key,OP);
obj.f2345(rand, res, ck, ik, ak);
String RES=DatatypeConverter.printHexBinary(res);
System.out.print(RES);


 
}*/

}





