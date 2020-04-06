<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" xml:lang="en" lang="en">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<link rel="stylesheet" type="text/css" href="${page.url_prefix}gnofract4d.css" media="screen"/>
<link rel="stylesheet" type="text/css" href="${page.url_prefix}print.css" media="print" />
<title>Gnofract 4D: Superior Fractal Software : ${page.name}</title>
<script src="http://www.google-analytics.com/urchin.js" type="text/javascript">
</script>
<script type="text/javascript">
_uacct = "UA-2808912-1";
urchinTracker();
</script>
</head>
<body>
<div id="wrap">

<div id="header">
<h1>Gnofract 4D</h1>
<p><strong>"There is no excellent beauty which hath not some strangeness in the proportion."</strong><br />(Francis Bacon)</p>
</div>

<img py:if="hasattr(page, 'image')" id="frontphoto" src="${page.url_prefix}${page.image}" width="760" height="175" alt="" />

<div id="avmenu">
<h2 class="hide">Menu:</h2>
<ul>
<li py:for="refpage in pages">
	<a py:if="refpage.file != page.file" href="${page.url_prefix}${refpage.file}">${refpage.name}</a>
	<span py:if="refpage.file == page.file">${refpage.name}</span>
</li>
<li>
	<a href="https://github.com/edyoung/gnofract4d/wiki">Wiki &amp; FAQ</a>
</li>
<li>
	<a href="https://github.com/edyoung/gnofract4d">GitHub Project Page</a>
</li>
</ul>
<h3 class="downloadbar"><a href="https://github.com/edyoung/gnofract4d/archive/v4.0.tar.gz">Download</a></h3>

<div class="announce" py:if="hasattr(page,'announce')">
<h3>Latest news:</h3>
<p py:for="announce in page.announce">
<strong>${announce.date}:</strong><br/>
${XML(announce.text)}
</p>
</div>

<div class="announce" py:if="hasattr(page,'comments')">
<p><strong>User comments:</strong></p>
<p py:for="comment in page.comments">
<element py:replace="XML(comment)"/>
</p>
</div>
</div>

<div id="content">
${XML(body)}
</div>

<div id="footer">
Hosted by GitHub
</div>

</div>
</body>
</html>
