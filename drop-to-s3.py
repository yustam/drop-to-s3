#!/usr/bin/python
# -*- coding: utf-8 -*-

"""s3 uploader"""

import os
import sys
import shutil
import random
import string
import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import QSettings


reload(sys)
sys.setdefaultencoding("UTF-8")
if boto.config.get('Boto', 'https_validate_certificates'):
    boto.config.set('Boto', 'https_validate_certificates', 'False')


class DropS3(QtGui.QWidget):
    def __init__(self):
        super(DropS3, self).__init__()
        self.initUI()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            settings = QSettings('jp.yustam.drop', 's3')
            access = str(settings.value('AccessKey', type=str))
            secret = str(settings.value('SecretKey', type=str))
            bucket = str(settings.value('BucketNeme', type=str))
            s3 = Uploader(access, secret, bucket)
            for url in e.mimeData().urls():
                print('[UPLOAD] ' + str(url.toLocalFile()))
                filename = str(url.toLocalFile())
                s3.upload_object(filename)
            print('[ OK ]')

    def initUI(self):
        self.setWindowTitle("Drop to S3")
        self.setGeometry(300, 300, 300, 150)

        self.access = QtGui.QPushButton('AccessKey', self)
        self.access.clicked.connect(self.show_access_dialog)

        self.secret = QtGui.QPushButton('SecretKey', self)
        self.secret.clicked.connect(self.show_secret_dialog)

        self.bucket = QtGui.QPushButton('BucketNeme', self)
        self.bucket.clicked.connect(self.show_bucket_dialog)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.access)
        layout.addWidget(self.secret)
        layout.addWidget(self.bucket)
        self.setLayout(layout)

        self.show()

    def show_access_dialog(self):
        self.show_dialog('AccessKey')

    def show_secret_dialog(self):
        self.show_dialog('SecretKey')

    def show_bucket_dialog(self):
        self.show_dialog('BucketNeme')

    def show_dialog(self, key):
        settings = QSettings('jp.yustam.drop', 's3')
        if settings.contains(key):
            value = settings.value(key, type=str)
            text, ok = QtGui.QInputDialog.getText(self, 'Settings', 'Input ' + key, text=value)
        else:
            text, ok = QtGui.QInputDialog.getText(self, 'Settings', 'Input ' + key)
        if ok:
            settings.setValue(key, text)


class Uploader():
    def __init__(self, acc, sec, bucket):
        self.conn = S3Connection(acc, sec)
        self.bucket = self.conn.get_bucket(bucket)
        self.threads = []

    def upload_object(self, filename):
        key = filename.decode('UTF-8')
        if os.path.isdir(key):
            print(' [D] ' + key)
            for child in os.listdir(key):
                self.upload_object(key + '/' + child)
        else:
            print('  [F] ' + key)
            thread = UploadThread(self.bucket, key, filename)
            self.threads.append(thread)
            thread.start()


class UploadThread(QtCore.QThread):
    def __init__(self, bucket, key, filename):
        QtCore.QThread.__init__(self)
        self.bucket = bucket
        self.key = key
        self.filename = filename

    def run(self):
        k = Key(self.bucket)
        k.key = os.environ['COMPUTERNAME'] + '/' + self.filename
        tmp = './tmp/' + self.random_str() + '.tmp'
        shutil.copyfile(self.key, tmp)
        k.set_contents_from_filename(tmp)
        os.remove(tmp)
        self.terminate()

    @staticmethod
    def random_str():
        return ''.join(random.choice(string.lowercase) for i in range(12))


def main():
    if not os.path.exists('./tmp/'):
        os.makedirs('./tmp/')
    app = QtGui.QApplication(sys.argv)
    drop = DropS3()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()