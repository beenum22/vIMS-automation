package com.xflowresearch.nfv.testertool.ue.nas;
import com.xflowresearch.nfv.testertool.ue.nas.RijndaelEngine;
import java.io.IOException;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;

import javax.crypto.BadPaddingException;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.xml.bind.DatatypeConverter;

import org.bouncycastle.crypto.BlockCipher;
import org.bouncycastle.crypto.CipherParameters;
import org.bouncycastle.crypto.DataLengthException;
import org.bouncycastle.crypto.params.KeyParameter;
import org.bouncycastle.util.encoders.Hex;
import org.bouncycastle.util.test.SimpleTestResult;

import com.xflowresearch.nfv.testertool.ue.nas.RijndaelEngine;

public class RijnImp {
       
	
	public void setRijEngine(byte [] key,BlockCipher Rij)
	{
		KeyParameter kp=new KeyParameter(key);
		Rij.init(true, kp);   //forencryption true by default (this also generates the working key)
	}
	
	
	  public byte [] RijndaelEncrypt(byte[]key, byte[]text,BlockCipher Rij)
	  {
		  boolean forEncryption= true;
    	  KeyParameter kp=new KeyParameter(key);
    	  Rij.init(forEncryption, kp);
    	  byte [] res = new byte [16];
    	  Rij.processBlock(text, 0, res, 0);
		  return res; 	
	  }
	  
	  public byte [] RijndaelDecrypt(byte[]key, byte[]ciph,BlockCipher Rij)
	  {
		  boolean forEncryption= false;

    	  KeyParameter kp=new KeyParameter(key);
    	  Rij.init(forEncryption, kp);
    	  byte [] res = new byte [16];
    	  Rij.processBlock(ciph, 0, res, 0);
		  return res; 	
	  }
	






	/*public static void main(String[] args){
		
		byte[] OP = {(byte)0x19,(byte)0x18,(byte)0xb8,(byte)0x40,(byte)0x19,(byte)0x5c,(byte)0x97,(byte)0x01,(byte)0x72,(byte)0x28,(byte)0x12,(byte)0x70,(byte)0x09,(byte)0xca,(byte)0x19,(byte)0x4e};
		byte [] key= {(byte)118, (byte) 123,(byte) 23,(byte) 17,(byte) 161, (byte)152, (byte)35, (byte)68, (byte)126, (byte)213, (byte)16, (byte)115, (byte)68, (byte)217, (byte)58, (byte)108, (byte)56, (byte)218, (byte)5, (byte)78, (byte)28, (byte)128, (byte)113, (byte)208, (byte)61, (byte)56, (byte)10, (byte)87, (byte)187, (byte)162, (byte)233, (byte)38 };
	    
		BlockCipher Rij=new RijndaelEngine();
		System.out.println(javax.xml.bind.DatatypeConverter.printHexBinary(OP));
		AuthAlgo obj =new AuthAlgo();
		byte [] encrypted =obj.RijndaelEncrypt(key ,OP,Rij);
		System.out.println(javax.xml.bind.DatatypeConverter.printHexBinary(encrypted));
		byte [] decrypted =obj.RijndaelDecrypt(key, encrypted,Rij);
		System.out.println(javax.xml.bind.DatatypeConverter.printHexBinary(decrypted));
  
    	}*/
    
    
        
       
    }
