public class TaskHelper {
    public static void main(String[] args) {
        if(args.length == 0){ System.out.println("Low"); return; }
        String d = args[0].toLowerCase();
        if(d.contains("today")) System.out.println("High");
        else if(d.contains("tomorrow")) System.out.println("Medium");
        else System.out.println("Low");
    }
}
