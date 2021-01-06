import os
for i, filename in enumerate(os.listdir("test")):

    #print(filename[-4:])
    if filename[-4:] == '.png':
        os.rename('test' + "/" + filename,'test' + "/" + str(i) + ".png")
    else:
        os.rename('test' + "/" + filename, 'test' + "/" + str(i) + ".jpg")

