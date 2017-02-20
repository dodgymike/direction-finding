import sys
import struct
import os
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

from math import pow, sqrt

class IQWindow(QtGui.QWidget):
	def __init__(self, iq_filename, mode):
		super(IQWindow, self).__init__()
		self.iq_filename = iq_filename
                self.mode = int(mode)

		print "iq_file_name (" + self.iq_filename + ")"
                self.iq_file_size = os.path.getsize(self.iq_filename)
                print "iq_file_size (" + str(self.iq_file_size) + ")"

		self.plotWidth = 1000000
		self.streamCount = 2
		self.floatByteCount = 4
		self.iqSliceSize = self.streamCount * self.floatByteCount * self.mode
		self.iq_data_a = []
		self.iq_data_b = []

		print "populating iq summary data"
#		self.populate_iq_summary_data()


		print "opening file"
		self.iq_file = open(self.iq_filename, 'rb')
		print "reading data"
		self.read_data(0)

		print "initialising UI"
		self.init_ui()

	def populate_iq_summary_data(self):
		self.iq_summary_data_a = []
		self.iq_summary_data_b = []

		iq_file = open(self.iq_filename, 'rb')

		totalIqSlices = self.iq_file_size / self.iqSliceSize
		print "total iq slices (" + str(totalIqSlices) + ")"
		i_sum_a = 0
		q_sum_a = 0
		i_sum_b = 0
		q_sum_b = 0

		sample_width = self.plotWidth
		start_slice = 0
		#start_slice = int(totalIqSlices / 7) - 2
		iq_file.seek(start_slice * self.iqSliceSize)
		#end_slice = int(totalIqSlices / 6) - 2
		end_slice = totalIqSlices - 2

		print "FF (" + ('f' * self.streamCount) + ")"
		print "start slice (" + str(start_slice) + ") end slice (" + str(end_slice) + ")"
		print "iqSliceSize (" + str(self.iqSliceSize) + ")"

		sliceIndex = start_slice

		while sliceIndex <= end_slice:
			print "iq slice number (" + str(sliceIndex) + ")"

			sliceIqDataRAW = iq_file.read(sample_width * self.iqSliceSize)
			sliceIqDataRAWLength = len(sliceIqDataRAW)
			sliceIqDataRAWLengthFloatCount = sliceIqDataRAWLength / self.floatByteCount
			print "sliceIqDataRAW length (" + str(sliceIqDataRAWLength) + ")"
			print "sliceIqDataRAWLengthFloatCount (" + str(sliceIqDataRAWLengthFloatCount) + ")"

			if sliceIqDataRAWLengthFloatCount < (self.plotWidth * self.streamCount):
				break

			sliceIqData = struct.unpack('f' * sliceIqDataRAWLengthFloatCount, sliceIqDataRAW)

			for sliceFloatIndex in range(0, sliceIqDataRAWLengthFloatCount, self.streamCount * self.mode):
				i_a = sliceIqData[sliceFloatIndex]
				q_a = sliceIqData[sliceFloatIndex + 1]
				i_b = sliceIqData[sliceFloatIndex + 2]
				q_b = sliceIqData[sliceFloatIndex + 3]

				i_sum_a += i_a
				q_sum_a += q_a
				i_sum_b += i_b
				q_sum_b += q_b
				
			average_a = i_sum_a / sample_width
			average_b = i_sum_b / sample_width

			print "average_a (" + str(average_a) + ") average_b (" + str(average_b) + ")"

			self.iq_summary_data_a.append(average_a)
			self.iq_summary_data_b.append(average_b)

     			i_sum_a = 0
			q_sum_a = 0
			i_sum_b = 0
			q_sum_b = 0

			sliceIndex += sample_width

		print "done populating iq summary with a len (" + str(len(self.iq_summary_data_a)) + ") b len (" + str(len(self.iq_summary_data_b)) + ")"

	def read_data(self, offset):
		if(offset >= self.iq_file_size):
			return

		self.iq_file.seek(offset * self.iqSliceSize)

		iq_file_float_count = self.plotWidth * self.streamCount * self.mode 

		floatData = self.iq_file.read(self.plotWidth * self.iqSliceSize)
		print "got floatData with length (" + str(len(floatData)) + ")"
		#if(len(floatData) == 0):
		#	return

		self.iq_data = struct.unpack('f' * iq_file_float_count, floatData)
		#self.iq_data = struct.unpack('f' * iq_file_float_count, self.iq_file.read(self.plotWidth * self.iqSliceSize))

		self.iq_data_a = []
		self.iq_data_b = []

		if self.mode == 1:
			print "MODE 1"
			for i in range(0, len(self.iq_data), 2):
				self.iq_data_a.append(self.iq_data[i])
				self.iq_data_b.append(self.iq_data[i + 1])
		else:
			print "MODE 2"
			for i in range(0, len(self.iq_data), 4):
				i_a = self.iq_data[i]
				q_a = self.iq_data[i + 1]
				amplitude_a = sqrt(pow(i_a, 2) + pow(q_a, 2))
				self.iq_data_a.append(amplitude_a)

				i_b = self.iq_data[i + 2]
				q_b = self.iq_data[i + 3]
				amplitude_b = sqrt(pow(i_b, 2) + pow(q_b, 2))
				self.iq_data_b.append(amplitude_b)

		self.normalise_iq_data()

	def normalise_iq_data(self):
		iq_data_a_range = self.normalise_array(self.iq_data_a)
		iq_data_b_range = self.normalise_array(self.iq_data_b)

		print "iq_data_a_range (" + str(iq_data_a_range) + ") iq_data_b_range (" + str(iq_data_b_range) + ")"

		max_range = iq_data_a_range
		if iq_data_b_range > max_range:
			max_range = iq_data_b_range

		for i in range(0, len(self.iq_data_a)):
			self.iq_data_a[i] += max_range

	def normalise_array(self, array_to_normalise):
		max = -sys.maxint
		min = sys.maxint
		sum = 0
		array_size = len(array_to_normalise)
		
		for i in range(0, array_size):
			current_value = array_to_normalise[i]
			if(current_value > max):
				max = current_value
			if(current_value < min):
				min = current_value
			sum += current_value

		average = sum / array_size
		array_range = max - min

	 	array_range_multiplier = 1.0 / array_range

		for i in range(0, array_size):
			array_to_normalise[i] -= average
			array_to_normalise[i] *= array_range_multiplier

		return array_range

	def init_ui(self):
		print "adding buttons"
		buttonNext = QtGui.QPushButton('Next')
		buttonNext.clicked.connect(self.handleButtonNext)

		buttonPrevious = QtGui.QPushButton('Previous')
		buttonPrevious.clicked.connect(self.handleButtonPrevious)

		buttonNext10 = QtGui.QPushButton('Next 10')
		buttonNext10.clicked.connect(self.handleButtonNext10)

		buttonPrevious10 = QtGui.QPushButton('Previous 10')
		buttonPrevious10.clicked.connect(self.handleButtonPrevious10)

		buttonNext100 = QtGui.QPushButton('Next 100')
		buttonNext100.clicked.connect(self.handleButtonNext100)

		buttonPrevious100 = QtGui.QPushButton('Previous 100')
		buttonPrevious100.clicked.connect(self.handleButtonPrevious100)

		#1000TVL == 976 x 582

		self.plotStartIndex = 0

		print "adding p1"
		p1 = pg.PlotWidget()
		p1.setClipToView(True)
		p1.setRange(xRange=[0, self.plotWidth], yRange=[-5, 5])
		p1.addLegend()
		self.p1 = p1

		self.p1PlotCurveA = pg.PlotCurveItem(pen='g', name='signal a')
		self.p1.addItem(self.p1PlotCurveA)
		self.p1PlotCurveB = pg.PlotCurveItem(pen='r', name='signal b')
		self.p1.addItem(self.p1PlotCurveB)

		self.p1PlotCurveA.setData(self.iq_data_a[self.plotStartIndex:self.plotWidth])
		self.p1PlotCurveB.setData(self.iq_data_b[self.plotStartIndex:self.plotWidth])

#		print "adding p2"
#		p2 = pg.PlotWidget()
#		p2.setClipToView(True)
#		#p2.setRange(xRange=[0, len(self.iq_summary_data_a)], yRange=[-5, 5])
#		p2.setRange(xRange=[0, self.plotWidth], yRange=[-5, 5])
#		p2.addLegend()
#		self.p2 = p2
#
#		self.p2PlotCurveA = pg.PlotCurveItem(pen='g', name='signal a')
#		self.p2.addItem(self.p2PlotCurveA)
#		self.p2PlotCurveB = pg.PlotCurveItem(pen='r', name='signal b')
#		self.p2.addItem(self.p2PlotCurveB)

#		self.p2PlotCurveA.setData(self.iq_summary_data_a)
#		self.p2PlotCurveB.setData(self.iq_summary_data_b)

		print "setting layouts"
		layout = QtGui.QGridLayout()
		self.setLayout(layout)

		print "adding widgets"
#		layout.addWidget(p2, 0, 0, 1, 2)
		layout.addWidget(p1, 1, 0, 1, 2)
		layout.addWidget(buttonPrevious, 2, 0)
		layout.addWidget(buttonNext, 2, 1)
		layout.addWidget(buttonPrevious10, 3, 0)
		layout.addWidget(buttonNext10, 3, 1)
		layout.addWidget(buttonPrevious100, 4, 0)
		layout.addWidget(buttonNext100, 4, 1)

		print "showing widgets"
		self.show()

	def handleButtonNext(self):
		self.plotStartIndex += self.plotWidth
		#if(self.plotStartIndex > len(self.iq_data_a)):
		#	self.plotStartIndex = 0

		self.handleButton()

	def handleButtonPrevious(self):
		self.plotStartIndex -= self.plotWidth
		if(self.plotStartIndex < 0):
			self.plotStartIndex = self.iq_file_size - self.plotWidth - 1

		self.handleButton()

	def handleButtonNext10(self):
		self.plotStartIndex += (self.plotWidth * 10)
		#if(self.plotStartIndex > len(self.iq_data_a)):
		#	self.plotStartIndex = 0

		self.handleButton()

	def handleButtonPrevious10(self):
		self.plotStartIndex -= (self.plotWidth * 10)
		if(self.plotStartIndex < 0):
			self.plotStartIndex = self.iq_file_size - self.plotWidth - 1

		self.handleButton()

	def handleButtonNext100(self):
		self.plotStartIndex += (self.plotWidth * 100)
		#if(self.plotStartIndex > len(self.iq_data_a)):
		#	self.plotStartIndex = 0

		self.handleButton()

	def handleButtonPrevious100(self):
		self.plotStartIndex -= (self.plotWidth * 100)
		if(self.plotStartIndex < 0):
			self.plotStartIndex = self.iq_file_size - self.plotWidth - 1

		self.handleButton()

	def handleButton(self):
		print "start index (" + str(self.plotStartIndex) + ")"

		self.read_data(self.plotStartIndex)
		self.p1PlotCurveA.setData(self.iq_data_a)
		self.p1PlotCurveB.setData(self.iq_data_b)


		self.p1.setRange(xRange=[0, self.plotWidth], yRange=[-5, 5])

def main():
	filename = sys.argv[1]
        mode = sys.argv[2]

	app = QtGui.QApplication(sys.argv)
	app.setApplicationName('Blerg')
	#ex= IQWindow("/home/iq/remote-dual-stream-433M+924k-200k-20161225-2.mag")
	#ex= IQWindow("/home/iq/remote-dual-stream-433M-8M-20161225-2.mag")
	ex= IQWindow(filename, mode)
	sys.exit(app.exec_())

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
#    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#        QtGui.QApplication.instance().exec_()
	main()

