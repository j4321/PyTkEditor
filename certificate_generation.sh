#! /bin/bash
# -*- coding:Utf-8 -*-

openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj '/C=FR/ST=France/L=Grenoble/O=PyTkEditor/OU=PyTkEditor_Server/CN=PyTkEditor_Server'
openssl x509 -signkey server.key -in server.csr -req -days 365 -out server.pem
cat server.pem server.key > server.crt
rm server.pem server.key server.csr 

openssl req -newkey rsa:2048 -nodes -keyout client.key -out client.csr  -subj '/C=FR/ST=France/L=Grenoble/O=PyTkEditor/OU=PyTkEditor_Client/CN=PyTkEditor_Client'
openssl x509 -signkey client.key -in client.csr -req -days 365 -out client.pem
cat client.pem client.key > client.crt
rm client.pem client.key client.csr
