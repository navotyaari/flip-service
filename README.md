# Flip Server Exercise

## Temporal Docs
A great part of this exercise is to learn some basic Temporal skills.
You don't need to understand everything about Temporal, but you should be able to understand the below
in order to complete the exercise.
- The docs in the tutorials here should be enough for this exercise: https://learn.temporal.io/getting_started/
 - Note that there are multiple SDKs for temporal, we are working with Python.
 - The section about Temporal Cloud is not needed for this exercise.
- There is some sample code in temporal SDK github repo: https://github.com/temporalio/samples-python

## Excercise Description

You are given black-box "flip" server - a remote, unreliable & quirky server that flips strings. See [server quirks](#server-quirks) for more details.

Your task is to utilize [temporal.io](https://temporal.io) to create a service that interacts with the server and reliably flips strings.

### Requirements

1. Accept arbitrary number of strings to flip
1. Reliably flip all of them
1. Add temporal `query` for number of strings flipped so far (measures progress)
1. Add temporal `query` for number of `HTTP 200 OK` responses recieved so far from the unreliable server (you can think of it as "how much real work we caused the unreliable flip server to do")

The service is to be used as follows, with the included `client.py` -
```bash
$ poetry run python client.py "hello" "world"
> "olleh" "dlrow"
```

#### Using the queries

You'll need to use the `queries` you implemented. For that you'll be required to add code to `client.py`.
The new code will run an asynchronous loop that will query the workflow, and print the results (every `n` seconds).

### The provided code
You can add files as needed, but you are expected to use the provide template to fill in your solution.

- The server is provided as a black-box, you can't change it (server.py)
- The temporal worker (worker.py) is another python file you should run, note that it only knows 
  about the Workflow defined in `tmprl.workflow` once you have added new `activity` you must add 
  it to the `ACTIVITIES` the worker knows of.
- The client (client.py) is provided as a way to interact with the server, you can change it as 
  needed (for example to add the queries)
- `workflow.py` is a template for the workflow implementation, it contains a naive string 
  flipping logic that does not interact with the server, you should replace that logic with one 
  that interacts with the server of course.
- The provided code should execute fine. In addition to the python code, make sure to run the local 
  temporal server first. 

## Using the server

### How to run the server

```bash
poetry run python exercise/server.py
```

### Sending a request

```bash
curl "http://127.0.0.1:8000/flip" -H "Content-Type: application/json" -d '["hello", "world"]'
```

### Server quirks

1. some requests may randomly fail (return code 500)
1. requests take constant time to process
1. the server accepts only lowercase a-z strings (else return code 400)
1. the server might sometime fail to flip some strings (return code 200, in the response the 
   failed strings will be `"-"`)
1. the server accepts up to 10 strings at a time (else return code 400)

## Guidelines

The code should be what you'd consider "Production Grade" python.

Provide a README.md with instructions on how to run the code.

You are expected to understand every part of the code you submit.

### Good luck!
