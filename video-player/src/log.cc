#include "log.hh"

#include <boost/core/null_deleter.hpp>
#include <boost/date_time/posix_time/posix_time_types.hpp>
#include <boost/log/core.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/sinks.hpp>
#include <boost/log/support/date_time.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>

#include <iostream>

namespace logging = boost::log;
namespace sinks = boost::log::sinks;
namespace expr = boost::log::expressions;

void setupLogging() //boost::log::trivial::severity_level level)
{
    logging::core::get()->set_filter
    (
        logging::trivial::severity >= logging::trivial::info
    );
    logging::add_common_attributes();

    using text_sink = sinks::synchronous_sink< sinks::text_ostream_backend >;
    boost::shared_ptr<text_sink> sink = boost::make_shared< text_sink >();
    boost::shared_ptr< std::ostream > stream(&std::clog, boost::null_deleter());
    sink->locked_backend()->add_stream(stream);

    sink->set_formatter
    (
	expr::stream << \
	expr::format_date_time< boost::posix_time::ptime >("TimeStamp", "%Y-%m-%d %H:%M:%S.%f") \
	<< " "
	<< expr::smessage
    );
    logging::core::get()->add_sink(sink);
}


void LOG(const char* message) {
  BOOST_LOG_TRIVIAL(error) << message;
}
