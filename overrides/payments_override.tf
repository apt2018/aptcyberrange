resource "aws_route53_record" "payments" {
  zone_id = "${aws_route53_zone.terraform.zone_id}"
  name = "payments.fazio.com"
  type = "A"
  ttl = "300"
  records = ["${aws_instance.payments.private_ip}"]
  depends_on = ["aws_instance.payments", "aws_route53_zone.terraform"]
}

resource "aws_instance" "payments" {
  ami = "ami-5dc5d54b"
  instance_type = "t2.micro"
  security_groups = ["${aws_security_group.terraform.id}"]
  key_name = "key"
  subnet_id = "${aws_subnet.terraform.id}"
  associate_public_ip_address = true
  private_ip = "10.0.0.20"
  depends_on = ["aws_route_table.terraform", "aws_security_group.terraform", "aws_subnet.terraform"]

  connection {
    host = "${aws_instance.payments.public_ip}"
    type = "ssh"
    user = "ubuntu"
    private_key = "${file("key")}"
    agent = false
  }

  provisioner "file" {
    source = "ansible/payment-server"
    destination = "~"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo sed -i 's/127.0.0.1 localhost/127.0.0.1 payments/g' /etc/hosts",
      "sudo hostname payments",
      "sudo nohup python /home/ubuntu/payment-server/payment_server.py >/dev/null 2>&1 &",
      "sleep 1"
    ]
  }
}

output "payments ip" {
  value = "${aws_instance.payments.public_ip}"
}