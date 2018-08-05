import java.util.HashMap;
import java.util.Map;
import java.util.HashSet;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.tree.*;
import java.rmi.RemoteException;

public class TargetModel implements Model {
	
	private Map<String, String> machine;
	private Map<String, StitchParser.TacticContext> tactics;
	private HashSet<String> hooks;
	private AnsibleProbe ansibleProbe;
	private Map<String, Probe> otherProbe;
	private Map<String, Integer> timeThresholds;

	// TODO: implement a cache/memory of remote variables, updated by probes on each call

	public TargetModel (Map<String,String> serverIP) {
		machine = serverIP;
		tactics = new HashMap<>();
		hooks = new HashSet<>();
		hooks.add("hasCredential");
		System.out.println("Creating probe...");
		ansibleProbe = new AnsibleProbe(machine.get("ansible"), 15213); // magic number for port, hardcode ansible server
		// probe = new Probe("128.237.200.112", 15213); // testing only
		// probe = new Probe("18.204.18.19", 1099); // testing only
		System.out.println("probe created");
		otherProbe = ansibleProbe.getProbe();

		int webThreshold = (int) System.currentTimeMillis() + 20000;
		timeThresholds.put("webThreshold", webThreshold);
		int paymentThreshold = (int) System.currentTimeMillis() + 40000;
		timeThresholds.put("paymentThreshold", paymentThreshold);
		System.out.println("webThreshold: " + webThreshold);
		System.out.println("paymentThreshold: " + paymentThreshold);
	}

	@Override
	public Map<String, String> getMachines() {
		return machine;
	}

	@Override
	public Map<String, StitchParser.TacticContext> getTactics() {
		return tactics;
	}

	@Override
	public HashSet<String> checkHooks() {
		return hooks;
	}

	@Override
	public void addTactic(String name, StitchParser.TacticContext tree) {
		tactics.put(name, tree);
		System.out.println("Model: adding new tactic, name: "+name);
	}

	@Override
	public String getName() {
		return new String("TargetModel");
	}

	/*
	 * Implement all the hooks right here
	 */
	@Override
	public Integer execHook(String id) {
		if (id.equals("hasCard")) {
			System.out.println("execHook: hasCard"); // has card credential
			try {
				Integer retVal = ((BlackhatProbe)otherProbe.get("Blackhat")).checkFile("~/passwd") + 
							 ((BlackhatProbe)otherProbe.get("Blackhat")).checkFile("~/shadow");
				if (retVal != 2) {
					return 0;  
				} 
				return 1;
			} catch (RemoteException e) {
				e.printStackTrace();
			} 
		} 
		else if (id.equals("hasLog")) {
			System.out.println("execHook: hasLogFile"); // has log file
			try {
				Integer retVal = ((FtpProbe)otherProbe.get("Ftp")).checkFile("/upload/logs.txt");  
				return retVal; 
			} catch (RemoteException e) {
				e.printStackTrace();
			}
		} 
		else if (id.equals("hasWeb")) {
			System.out.println("execHook: hasWeb"); // has web credential
			try {
				Integer retVal = ((BlackhatProbe)otherProbe.get("Blackhat")).checkFile("~/logs_decoded.txt"); 
				return retVal; 
			} catch (RemoteException e) {
				e.printStackTrace();
			}
		} 
		else if (id.equals("suspicious")) {
			System.out.println("execHook: suspicious"); // has suspicious mail
			Integer retVal = ansibleProbe.checkSuspicious();
			return retVal;
		} 
		else if (id.equals("currentTime")) {
			System.out.println("execHook: currentTime"); // show current time
			return (int)System.currentTimeMillis();
		} 
		else if (id.equals("WEB_THRESHOLD")) {
			System.out.println("execHook: webThreshold"); // show web server's threshold
			return timeThresholds.get("webThreshold");
		}
		System.err.println("execHook: name of hook cannot be found");
		return -1;
	}

	/*
	 * Implement all operations right here
	 */
	@Override
	public Integer execOperations(String id) {
		if (id.equals("increaseWebThreshold")) {
			int webThreshold = timeThresholds.get("webThreshold");
			webThreshold += 2000;
			timeThresholds.put("webThreshold", webThreshold);
		} 
		if (id.equals("filterPhishingEmail")) {
			try {
				boolean conn = ConnectionSSH.connect("contractor", machine.get("contractor"), "python filterEmail.py");
				if (!conn) {
					System.err.println("session connection timeout, wrong IP address?");
					return 0;
				}
			} catch (Exception e) {
				e.printStackTrace();
			}
		} 
		if (id.equals("W.resetPassword")) {
			String newPassword = String.valueOf(System.currentTimeMillis() + 1);
			try {
				boolean conn = ConnectionSSH.connect("ansible", machine.get("ansible"), 
					"ansible-playbook inject/resetWebPassword.yml --extra-vars '{\"new_password\":newPassword}'");
				if (!conn) {
					System.err.println("session connection timeout, wrong IP address?");
					return 0;
				}
			} catch (Exception e) {
				e.printStackTrace();
			}
		} 
		if (id.equals("A.send")) {

		} 
		if (id.equals("sendPhishingEmail")) {

		} 
		if (id.equals("A.downloadLogFile")) {

		} 
		if (id.equals("A.decodeLogFile")) {

		} 
		if (id.equals("A.loginWeb")) {

		} 
		if (id.equals("A.injectShell")) {

		} 
		if (id.equals("A.crackPasswd")) {

		} 
		if (id.equals("A.storePasswd")) {

		} 
		if (id.equals("A.firmware")) {

		} 
		if (id.equals("A.transaction")) {

		}
		if (id.equals("A.deleteLogFile")) {

		}
		if (id.equals("A.deleteWebCredential")) {

		}
		if (id.equals("F.deleteLogFile")) {

		}
		return 1;
	}
}
