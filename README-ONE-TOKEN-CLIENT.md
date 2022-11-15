# One token / One client method

## Motivation

This method aims to generate private and public key pair for one specific client 
linked to one specific token. For instance, when a new client registers, he gets 
to choose a token name and from there a private and public key pair is generated.
It must be possible to know if the client is owner of this token by looking at 
his public key.


When doing a transaction, the transaction gets signed with the private key on a
trusted node. The transaction is then sent to other nodes which will check if the
signature is valid.

We need a way to say that a specific public key can generate stuff related to its
token without any restriction, without the private key being known by anyone.

If I can be able to detect that a public key is related to a specific token and 
a private key, without make the private key public, it is correct.

Get keys encoded by GTH private key so that we can check with public key that the key
is authentic. But still we need to integrate the token name in the public key.

## Method

The public key will now be in 2 parts :
- The first part is a standard public key
- The second part is the token name + public key signed with the private key of GTH
  - For non-admin this part can be anything encoded with their own key. Such as a 
    name or a random string. "casual" keyword is used to denote non-admin keys.