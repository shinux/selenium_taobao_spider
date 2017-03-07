
import time
import numpy as np
from scipy.stats import kendalltau
import seaborn as sns
from db import shoe_collection
sns.set(style="ticks")

x = []
y = []
for i in shoe_collection.find({ 'category': '斑马'}):
    x.append(int(i['price']))
    y.append(time.mktime(i['date'].timetuple()))

print(len(x))
print(y)
x = np.array(x)
y = np.array(y)

sns.jointplot(x, y, kind="hex", stat_func=kendalltau, color="#4CB391")
sns.plt.show()
